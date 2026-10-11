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
        target = Path(target_path).resolve()
        base = Path(workspace_root).resolve()
        return str(target.relative_to(base)).replace('\\', '/')
    except Exception:
        return str(target_path).replace('\\', '/')

def is_path_inside(target_path, base_path):
    try:
        target = Path(target_path).resolve()
        base = Path(base_path).resolve()
        return target == base or base in target.parents
    except Exception:
        return False

def is_secret_path(path_str):
    normalized = str(path_str).replace('\\', '/')
    secret_pattern = (
        r'(^|[\\\\/])(\.env(?!(\.example|\.sample|\.template))|'
        r'.*\.pem$|.*\.key$|.*\.p12$|.*\.pfx$|'
        r'id_rsa.*|id_ed25519.*|credentials.*\.json$|'
        r'\.npmrc$|\.pypirc$|.*\.tfstate$)'
    )
    return bool(re.search(secret_pattern, normalized, re.IGNORECASE))

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

    # Proibir flags com efeito de mutação / escrita
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
        # flags permitidas apenas de visualizacao
        allowed_status_flags = {'--short', '-s', '--branch', '-b', '--porcelain', '--porcelain=v1', '--porcelain=v2', '--ignored'}
        for a in args:
            if a.startswith('-') and a.lower() not in allowed_status_flags:
                return False
        return True

    if sub == 'diff':
        # diff sem --output, sem mutacoes
        for a in args:
            if a.startswith('-'):
                # permitidas: --stat, --cached, --staged, -p, -u, --name-only, --name-status, -w, --ignore-all-space
                if a.lower() not in ('--stat', '--cached', '--staged', '-p', '-u', '--name-only', '--name-status', '-w', '--ignore-all-space'):
                    # se for commit range ou flag numerica ex -U3
                    if not re.match(r'^-U\d+$', a):
                        return False
        return True

    if sub == 'log':
        # log sem execucao ou format com comandos
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
        # Apenas listagem ou show-current
        allowed_branch_args = {'--show-current', '-a', '--all', '-r', '--remotes', '-v', '-vv'}
        for a in args:
            if a.lower() not in allowed_branch_args:
                return False
        return True

    if sub == 'show':
        # show de commits / objetos sem --output
        for a in args:
            if a.startswith('-') and a.lower() not in ('--stat', '--oneline', '--name-only', '--name-status'):
                return False
        return True

    return False

def is_strictly_safe_unittest(cmd_str):
    if any(tok in cmd_str for tok in ('>', '<', '|', ';', '&', '`', '$', '\n', '\r')):
        return False
    # python -m unittest ...
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+-m\s+unittest(\s+[a-zA-Z0-9_\-\./\\:]+)*\s*$'
    if re.match(pattern, cmd_str, re.IGNORECASE):
        return True
    # node test runner padrao
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
    # python .agents/scripts/utf8_writer.py <evidence_target> <content>
    pattern = r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+(\.agents[\\/]scripts[\\/]|scripts[\\/])utf8_writer\.py\s+(evidence[\\/]|runs[\\/]|logs[\\/])[a-zA-Z0-9_\-\./\\]+\s+.*$'
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

        # Exceção controlada sob STOP ou ESCALATED/PAUSED: permitir APENAS leitura segura e registro de evidência
        if stop_exists or run_is_escalated_or_paused:
            state_label = "STOP ativo" if stop_exists else "Run em ESCALATED/PAUSED"
            if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
                path_val = args.get("AbsolutePath", args.get("SearchPath", args.get("DirectoryPath", "")))
                if path_val and is_secret_path(path_val):
                    emit_decision("deny", f"{state_label}: leitura de segredo bloqueada", tool_name)
                emit_decision("allow", f"{state_label}: leitura de diagnostico permitida", tool_name)
            if tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if is_strictly_safe_evidence_writer(cmd):
                    emit_decision("allow", f"{state_label}: registro de relatorio via utf8_writer permitido", tool_name)
                if is_strictly_safe_command(cmd):
                    emit_decision("allow", f"{state_label}: inspecao permitida", tool_name)
                emit_decision("deny", f"{state_label}: comando modificador bloqueado: {cmd}", tool_name)
            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                target = str(args.get("TargetFile", ""))
                rel_target = get_relative_target(target, workspace_root)
                if rel_target.startswith("runs/") or rel_target.startswith("evidence/") or rel_target.startswith("logs/"):
                    emit_decision("allow", f"{state_label}: registro de evidencia/relatorio de parada permitido", tool_name)
                emit_decision("deny", f"{state_label}: modificacao de arquivo bloqueada fora de evidencias: {rel_target}", tool_name)
            if tool_name == "invoke_subagent":
                emit_decision("deny", f"{state_label}: novas delegacoes de subagente bloqueadas", tool_name)
            emit_decision("deny", f"{state_label}: operacao {tool_name} bloqueada", tool_name)

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
                target_path = str(args.get("TargetFile", args.get("AbsolutePath", args.get("SearchPath", ""))))
                pat = rule.get("pattern", "")
                if target_path and pat and re.search(pat, target_path.replace('\\', '/'), re.IGNORECASE):
                    emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "command_regex" and tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                pat = rule.get("pattern", "")
                if cmd and pat and re.search(pat, cmd, re.IGNORECASE):
                    emit_decision("deny", reason, tool_name, rule_id)

            elif cond == "protect_org_active" and protect_org_active:
                target_path = ""
                if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                    target_path = str(args.get("TargetFile", ""))
                elif tool_name == "run_command":
                    cmd = str(args.get("CommandLine", ""))
                    if re.search(r'(\.agents|org_v5|AGENTS\.md)', cmd) and re.search(r'(git\s+apply|Remove-Item|rm|del|Set-Content|Out-File|echo\s+.*>|>>)', cmd):
                        emit_decision("deny", reason, tool_name, rule_id)
                if target_path:
                    rel_target = get_relative_target(target_path, workspace_root)
                    prefixes = rule.get("protected_prefixes", [".agents/", "org_v5/", "AGENTS.md"])
                    for pfx in prefixes:
                        if rel_target.startswith(pfx) or rel_target == pfx.rstrip('/'):
                            emit_decision("deny", f"PROTECT_ORG ativo: modificacao em {rel_target} bloqueada sem desbloqueio humano previo", tool_name, rule_id)

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
                path_val = args.get("AbsolutePath", args.get("SearchPath", args.get("DirectoryPath", "")))
                if path_val and is_secret_path(path_val):
                    emit_decision("deny", f"Acesso a arquivo de segredos bloqueado: {path_val}", tool_name, rule_id)
                emit_decision("allow", "Operacao segura de leitura e inspecao", tool_name, rule_id)

            elif cond == "strict_safe_command" and tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                subsystem = rule.get("subsystem", "")
                if is_strictly_safe_command(cmd, subsystem):
                    emit_decision("allow", f"Comando seguro aprovado pelo classificador ({subsystem or 'geral'})", tool_name, rule_id)

            elif cond == "workspace_internal_write":
                target = str(args.get("TargetFile", ""))
                if not target:
                    emit_decision("ask", "Arquivo de destino nao especificado", tool_name, rule_id)
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
