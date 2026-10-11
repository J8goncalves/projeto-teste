import sys
import json
import os
import re
import shlex
from pathlib import Path

def emit_decision(decision, reason, tool_name="", rule_id=""):
    out = {"decision": decision, "reason": reason}
    print(json.dumps(out))
    sys.exit(0)

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

def get_relative_target(target_path, workspace_root):
    try:
        base = Path(workspace_root).resolve()
        p = Path(target_path)
        if not p.is_absolute():
            target = (base / p).resolve()
        else:
            target = p.resolve()
        return str(target.relative_to(base)).replace('\\', '/')
    except Exception:
        return str(target_path).replace('\\', '/')

def is_path_inside(target_path, base_path):
    try:
        base = Path(base_path).resolve()
        p = Path(target_path)
        if not p.is_absolute():
            target = (base / p).resolve()
        else:
            target = p.resolve()
        target.relative_to(base)
        return True
    except Exception:
        return False

def is_secret_path(path_str):
    if not path_str:
        return False
    normalized = str(path_str).replace('\\', '/')
    secret_pattern = (
        r'(^|[\\\\/])(\.env(?!(\.example|\.sample|\.template))|'
        r'.*\.pem$|.*\.key$|.*\.p12$|.*\.pfx$|'
        r'id_rsa.*|id_ed25519.*|credentials.*\.json$|'
        r'\.npmrc$|\.pypirc$|.*\.tfstate$)'
    )
    return bool(re.search(secret_pattern, normalized, re.IGNORECASE))

def validate_workspace_path(path_str, workspace_root):
    """
    Confinamento canonico estrito em workspace_safe_path (F03).
    Resolve contra a raiz do workspace, verifica contencao estrita via relative_to
    e rejeita explicitamente caminhos e arquivos de segredos.
    """
    if not path_str or not isinstance(path_str, str) or not path_str.strip():
        return False, "Caminho ausente ou vazio"
    if '\x00' in path_str:
        return False, "Caractere nulo detectado no caminho"
    try:
        base = Path(workspace_root).resolve()
        p = Path(path_str.strip())
        if not p.is_absolute():
            target = (base / p).resolve()
        else:
            target = p.resolve()

        # Confinamento canonico estrito: falha se fora da raiz ou em outro drive
        target.relative_to(base)

        # Checagem de segredos no caminho original e no caminho canonico resolvido
        if is_secret_path(str(target)) or is_secret_path(path_str):
            return False, "Acesso a arquivo ou diretorio de segredos bloqueado por politica"

        return True, ""
    except ValueError:
        return False, f"Caminho fora dos limites canonicos do workspace: {path_str}"
    except Exception as e:
        return False, f"Falha na resolucao canonica do caminho: {str(e)}"

def extract_read_paths(tool_name, args):
    paths = []
    keys = ("AbsolutePath", "DirectoryPath", "SearchPath", "TargetFile", "filePath", "path", "dir_path", "file_path")
    for k in keys:
        if k in args:
            val = args[k]
            if isinstance(val, list):
                paths.extend([str(x) for x in val if x])
            elif isinstance(val, str) and val.strip():
                paths.append(val.strip())
    return paths

def extract_write_targets(args):
    targets = []
    if "TargetFile" in args and args["TargetFile"]:
        targets.append(str(args["TargetFile"]))
    if "TargetFiles" in args and isinstance(args["TargetFiles"], list):
        targets.extend([str(x) for x in args["TargetFiles"] if x])
    if "files" in args and isinstance(args["files"], list):
        targets.extend([str(x) for x in args["files"] if x])
    if "edits" in args and isinstance(args["edits"], list):
        for e in args["edits"]:
            if isinstance(e, dict):
                f = e.get("TargetFile", e.get("file", ""))
                if f:
                    targets.append(str(f))
    return targets

def load_policy_rules(workspace_root):
    policy_file = workspace_root / ".agents" / "policies" / "pretool_rules.json"
    if not policy_file.exists():
        return None
    try:
        policy_data = json.loads(policy_file.read_text(encoding="utf-8"))
        if not isinstance(policy_data, dict) or "version" not in policy_data:
            return None
        return policy_data
    except Exception:
        return None

def is_strictly_safe_git_command(cmd_str):
    # Proibir qualquer operador de pipeline, redirecionamento ou encadeamento
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False

    # Proibir flags com efeito de mutacao / escrita
    forbidden_flags = [
        '-o', '--output', '-m', '-M', '-d', '-D', '--delete',
        '-c', '--config', '--exec-path', '--upload-pack',
        '-a', '--all', '-f', '--force', '--hard', '--soft'
    ]
    for ff in forbidden_flags:
        if re.search(rf'(?:^|\s){re.escape(ff)}(?:\s|=|:|$)', cmd_str, re.IGNORECASE):
            return False

    try:
        parts = shlex.split(cmd_str, posix=False)
    except Exception:
        return False

    if not parts or parts[0].lower() not in ('git', 'git.exe'):
        return False

    if len(parts) == 1:
        return False

    sub = parts[1].lower()
    args = parts[2:]

    # Allowed safe subcommands: status, diff, log, branch, show
    if sub == 'status':
        allowed_status_flags = {'--short', '-s', '--branch', '-b', '--porcelain', '--porcelain=v1', '--porcelain=v2', '--ignored'}
        for a in args:
            if a.startswith('-') and a.lower() not in allowed_status_flags:
                return False
        return True

    if sub == 'diff':
        for a in args:
            if a.startswith('-'):
                if a.lower() not in ('--stat', '--cached', '--staged', '-p', '-u', '--name-only', '--name-status', '-w', '--ignore-all-space'):
                    if not re.match(r'^-U\d+$', a):
                        return False
        return True

    if sub == 'log':
        i = 0
        while i < len(args):
            a = args[i]
            if a in ('-n', '-N'):
                if i + 1 < len(args) and args[i+1].isdigit():
                    i += 2
                    continue
                return False
            elif a.startswith('-'):
                if not (re.match(r'^-[nN]\d+$', a) or re.match(r'^-\d+$', a) or a.lower() in ('--oneline', '--stat', '--graph', '--name-only', '--name-status')):
                    return False
            i += 1
        return True

    if sub == 'branch':
        allowed_branch_args = {'--show-current', '-a', '--all', '-r', '--remotes', '-v', '-vv'}
        for a in args:
            if a.lower() not in allowed_branch_args:
                return False
        return True

    if sub == 'show':
        for a in args:
            if a.startswith('-') and a.lower() not in ('--stat', '--oneline', '--name-only', '--name-status'):
                return False
        return True

    return False

def is_strictly_safe_unittest(cmd_str):
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+-m\s+unittest(\s+[a-zA-Z0-9_\-\./\\:]+)*\s*$'
    if re.match(pattern, cmd_str, re.IGNORECASE):
        return True
    pattern_node = r'^\s*(["\']?[^"\']*[\\/])?node(\.exe)?["\']?\s+tests[\\/][a-zA-Z0-9_\-\.]+\.js\s*$'
    return bool(re.match(pattern_node, cmd_str, re.IGNORECASE))

def is_strictly_safe_control_plane(cmd_str):
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+-m\s+org_v5\.cli\s+(report|status|validate|events|run-tests)(\s+[a-zA-Z0-9_\-\./\\:=]+)*\s*$'
    return bool(re.match(pattern, cmd_str, re.IGNORECASE))

def is_strictly_safe_evidence_writer(cmd_str):
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False
    # Suporta tanto --target <path> quanto argumento posicional
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+(\.agents[\\/]scripts[\\/]|scripts[\\/])utf8_writer\.py\s+(--target\s+|=)?["\']?(evidence[\\/]|runs[\\/]|logs[\\/])[a-zA-Z0-9_\-\./\\]+["\']?\s+.*$'
    return bool(re.match(pattern, cmd_str, re.IGNORECASE))

def is_strictly_safe_which_where(cmd_str):
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False
    pattern = r'^\s*(where|which)(\.exe)?\s+[a-zA-Z0-9_\-\.]+\s*$'
    return bool(re.match(pattern, cmd_str, re.IGNORECASE))

def is_strictly_safe_command(cmd_str, subsystem=""):
    if not subsystem:
        return (
            is_strictly_safe_git_command(cmd_str) or
            is_strictly_safe_unittest(cmd_str) or
            is_strictly_safe_control_plane(cmd_str) or
            is_strictly_safe_evidence_writer(cmd_str) or
            is_strictly_safe_which_where(cmd_str)
        )
    if subsystem == "git":
        return is_strictly_safe_git_command(cmd_str)
    if subsystem == "unittest":
        return is_strictly_safe_unittest(cmd_str)
    if subsystem == "control_plane":
        return is_strictly_safe_control_plane(cmd_str)
    if subsystem == "evidence_writer":
        return is_strictly_safe_evidence_writer(cmd_str)
    if subsystem == "which_where":
        return is_strictly_safe_which_where(cmd_str)
    return False

def is_read_only_incident_command(cmd_str):
    """
    Classificador estrito e exclusivo para estados STOP, PAUSED e ESCALATED (F02).
    Nega interpretadores, suites de teste e scripts mutaveis por padrao.
    Permite unicamente inspecao pura de git (status, diff, log, branch, show) ou which/where.
    """
    # Proibir qualquer operador de pipeline, redirecionamento ou encadeamento
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False

    # Proibir expressamente qualquer interpretador de teste ou runner
    if re.search(r'\bunittest\b|\bnode(\.exe)?\b|\brun-tests\b', cmd_str, re.IGNORECASE):
        return False

    # Proibir interpretadores executando scripts ou comandos inline arbitrários
    if re.search(r'python(\.exe)?\s+(-c|-m|\S+\.py)|node(\.exe)?\s+(\S+\.js|-e|--eval)|powershell|pwsh|cmd(\.exe)?|sh\b|bash\b', cmd_str, re.IGNORECASE):
        return False

    # Permitir exclusivamente visualizacao pura via git ou which/where
    return is_strictly_safe_git_command(cmd_str) or is_strictly_safe_which_where(cmd_str)

def is_safe_incident_evidence_writer(cmd_str, workspace_root):
    """
    Valida chamada a utf8_writer.py sob incidentes (F02/Fase B).
    Permite apenas gravacao direcionada estritamente a evidence/, runs/ ou logs/
    dentro do workspace canonico, sem qualquer escape (..) ou redirecionamento.
    Suporta --target <path> e argumento posicional.
    """
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False

    # Regex que extrai o alvo suportando --target <path> ou posicional
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+(\.agents[\\/]scripts[\\/]|scripts[\\/])utf8_writer\.py\s+(?:--target\s+|--target=)?["\']?([^\s"\']+)["\']?\s+.*$'
    m = re.match(pattern, cmd_str, re.IGNORECASE)
    if not m:
        return False
    target_rel = m.group(4).replace('\\', '/')
    if '..' in target_rel.split('/'):
        return False
    if not (target_rel.startswith("evidence/") or target_rel.startswith("runs/") or target_rel.startswith("logs/")):
        return False
    try:
        base = Path(workspace_root).resolve()
        target = (base / target_rel).resolve()
        target.relative_to(base)
        return True
    except Exception:
        return False

def matches_tool(rule_tools, tool_name):
    return "*" in rule_tools or tool_name in rule_tools

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            emit_decision("ask", "Entrada vazia em stdin: confirmacao requerida")

        try:
            data = json.loads(raw_input)
        except Exception as pe:
            emit_decision("deny", f"Payload JSON malformado: {str(pe)}")

        workspace_root = resolve_workspace_root(data)
        tool_call = data.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        # Carregar política declarativa pretool_rules.json (P0 - R01)
        policy = load_policy_rules(workspace_root)
        if policy is None:
            emit_decision("deny", "Politica declarativa (.agents/policies/pretool_rules.json) ausente ou invalida")

        # 1. Checagens de Contexto Operacional
        stop_file = workspace_root / ".agents" / "state" / "STOP"
        stop_exists = stop_file.exists()

        run_is_escalated_or_paused = False
        curr_run_file = workspace_root / "runs" / "CURRENT"
        if curr_run_file.exists():
            try:
                run_id = curr_run_file.read_text(encoding="utf-8").strip()
                state_file = workspace_root / "runs" / run_id / "state.json"
                if state_file.exists():
                    st = json.loads(state_file.read_text(encoding="utf-8"))
                    phase = st.get("phase", st.get("status", ""))
                    if phase in ("ESCALATED", "PAUSED"):
                        run_is_escalated_or_paused = True
            except Exception:
                run_is_escalated_or_paused = True

        protect_org_file = workspace_root / ".agents" / "state" / "PROTECT_ORG"
        protect_org_active = protect_org_file.exists()

        # F02: Exceção de incidente sob STOP ou ESCALATED/PAUSED: permitir APENAS leitura segura e registro de evidência
        if stop_exists or run_is_escalated_or_paused:
            state_label = "STOP ativo" if stop_exists else "Run em ESCALATED/PAUSED"
            if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
                paths = extract_read_paths(tool_name, args)
                if not paths:
                    emit_decision("deny", f"{state_label}: caminho ausente ou nao especificado para {tool_name}", tool_name)
                for p in paths:
                    ok, reason = validate_workspace_path(p, workspace_root)
                    if not ok:
                        emit_decision("deny", f"{state_label}: {reason}", tool_name)
                emit_decision("allow", f"{state_label}: leitura de diagnostico permitida", tool_name)

            if tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if is_safe_incident_evidence_writer(cmd, workspace_root):
                    emit_decision("allow", f"{state_label}: registro de relatorio via utf8_writer permitido", tool_name)
                if is_read_only_incident_command(cmd):
                    emit_decision("allow", f"{state_label}: comando de diagnostico somente-leitura permitido", tool_name)
                emit_decision("deny", f"{state_label}: comando bloqueado durante estado de parada/incidente: {cmd}", tool_name)

            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                targets = extract_write_targets(args)
                if not targets:
                    emit_decision("deny", f"{state_label}: destino nao especificado", tool_name)
                for target in targets:
                    rel_target = get_relative_target(target, workspace_root)
                    if '..' in rel_target.split('/'):
                        emit_decision("deny", f"{state_label}: escape de caminho rejeitado", tool_name)
                    if not is_path_inside(target, workspace_root) or not (rel_target.startswith("runs/") or rel_target.startswith("evidence/") or rel_target.startswith("logs/")):
                        emit_decision("deny", f"{state_label}: modificacao de arquivo bloqueada fora de evidencias: {rel_target}", tool_name)
                emit_decision("allow", f"{state_label}: registro de evidencia/relatorio de parada permitido", tool_name)

            if tool_name in ("invoke_subagent", "define_subagent", "schedule"):
                emit_decision("deny", f"{state_label}: operacao de subagente/agendamento bloqueada", tool_name)

            emit_decision("deny", f"{state_label}: operacao {tool_name} bloqueada por estado de parada", tool_name)

        # 2. Avaliação de DENY RULES declarativas (Precedência 1 - DENY)
        for rule in policy.get("deny_rules", []):
            rule_id = rule.get("id", "")
            rule_tools = rule.get("tools", [])
            if not matches_tool(rule_tools, tool_name):
                continue

            cond = rule.get("condition", "")
            reason = rule.get("reason", "Bloqueado por regra de seguranca")

            if cond == "always":
                emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "stop_file_exists" and stop_exists:
                emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "run_escalated_or_paused" and run_is_escalated_or_paused:
                emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "path_regex":
                targets = extract_read_paths(tool_name, args) or extract_write_targets(args)
                pat = rule.get("pattern", "")
                if targets and pat:
                    for t in targets:
                        if re.search(pat, t.replace('\\', '/'), re.IGNORECASE):
                            emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "command_regex" and tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                pat = rule.get("pattern", "")
                if cmd and pat and re.search(pat, cmd, re.IGNORECASE):
                    emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "protect_org_active" and protect_org_active:
                if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                    targets = extract_write_targets(args)
                    if not targets:
                        emit_decision("deny", "PROTECT_ORG ativo: destino de escrita nao especificado", tool_name, rule_id)
                    prefixes = rule.get("protected_prefixes", [".agents/", "org_v5/", "AGENTS.md"])
                    for target_path in targets:
                        rel_target = get_relative_target(target_path, workspace_root)
                        for pfx in prefixes:
                            if rel_target.startswith(pfx) or rel_target == pfx.rstrip('/'):
                                emit_decision("deny", f"PROTECT_ORG ativo: modificacao em {rel_target} bloqueada sem desbloqueio humano previo", tool_name, rule_id)

                elif tool_name == "run_command":
                    cmd = str(args.get("CommandLine", ""))
                    # Excetuar comandos estritamente seguros de leitura/testes do control plane ou git
                    if is_strictly_safe_control_plane(cmd) or is_strictly_safe_git_command(cmd):
                        pass
                    else:
                        has_core_ref = bool(re.search(r'(\.agents|org_v5|AGENTS\.md|PROTECT_ORG)', cmd, re.IGNORECASE))
                        if has_core_ref:
                            mutating_patterns = [
                                r'python(\.exe)?\s+-c',
                                r'node(\.exe)?\s+(-e|--eval)',
                                r'\b(powershell|pwsh|cmd(\.exe)?)\b',
                                r'\b(Remove-Item|rm|del|erase|rd|rmdir|touch|Move-Item|mv|move|Copy-Item|cp|copy|Set-Content|Add-Content|Out-File|New-Item|Clear-Content|tee)\b',
                                r'(>|>>)',
                                r'git\s+(apply|checkout|restore|clean|rm|commit|reset|branch\s+(-[dDmM]))',
                                r'\b(unlink|remove|truncate|write_text|write_bytes)\b'
                            ]
                            for mp in mutating_patterns:
                                if re.search(mp, cmd, re.IGNORECASE):
                                    emit_decision("deny", f"PROTECT_ORG ativo: comando com mutacao potencial direcionada ao Core bloqueado: {cmd}", tool_name, rule_id)

        # 3. Avaliação de FORCE_ASK RULES declarativas (Precedência 2 - FORCE_ASK)
        for rule in policy.get("force_ask_rules", []):
            rule_id = rule.get("id", "")
            rule_tools = rule.get("tools", [])
            if not matches_tool(rule_tools, tool_name):
                continue
            cond = rule.get("condition", "")
            reason = rule.get("reason", "Confirmacao humana explicita requerida")

            if cond == "command_regex" and tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                pat = rule.get("pattern", "")
                if cmd and pat and re.search(pat, cmd.strip(), re.IGNORECASE):
                    emit_decision("force_ask", reason, tool_name, rule_id)

        # 4. Avaliação de ALLOW RULES declarativas (Precedência 3 - ALLOW estrito)
        for rule in policy.get("allow_rules", []):
            rule_id = rule.get("id", "")
            rule_tools = rule.get("tools", [])
            if not matches_tool(rule_tools, tool_name):
                continue
            cond = rule.get("condition", "")

            if cond == "always":
                emit_decision("allow", "Aprovado por regra declarativa", tool_name, rule_id)

            elif cond == "workspace_safe_path":
                paths = extract_read_paths(tool_name, args)
                if not paths:
                    emit_decision("deny", f"Caminho ausente ou nao especificado para {tool_name}", tool_name, rule_id)
                for p in paths:
                    ok, reason = validate_workspace_path(p, workspace_root)
                    if not ok:
                        emit_decision("deny", reason, tool_name, rule_id)
                emit_decision("allow", "Operacao segura de leitura e inspecao confinada ao workspace", tool_name, rule_id)

            elif cond == "strict_safe_command" and tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                subsystem = rule.get("subsystem", "")
                if is_strictly_safe_command(cmd, subsystem):
                    emit_decision("allow", f"Comando seguro aprovado pelo classificador ({subsystem or 'geral'})", tool_name, rule_id)

            elif cond == "workspace_internal_write":
                targets = extract_write_targets(args)
                if not targets:
                    emit_decision("ask", "Arquivo de destino nao especificado", tool_name, rule_id)
                for target in targets:
                    if not is_path_inside(target, workspace_root):
                        emit_decision("deny", f"Modificacao fora dos limites do workspace bloqueada: {target}", tool_name, rule_id)
                emit_decision("allow", "Modificacao de arquivo dentro do workspace aprovada", tool_name, rule_id)

        # 5. Default Fallback Seguro para operações não classificadas: ASK (P0 - R02)
        if tool_name == "run_command":
            cmd = str(args.get("CommandLine", ""))
            emit_decision("ask", f"Comando fora da faixa allow segura: confirmacao recomendada: {cmd[:100]}", tool_name)

        emit_decision("ask", f"Ferramenta desconhecida ou nao classificada ({tool_name}): requer confirmacao", tool_name)

    except Exception as e:
        emit_decision("deny", f"Falha interna do pretool_guard: {str(e)}")

if __name__ == "__main__":
    main()
