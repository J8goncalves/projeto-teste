import sys
import json
import os
import re
from pathlib import Path

def emit_decision(decision, reason, tool_name=""):
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

def is_safe_inspection_command(command_str):
    # Check for shell redirection or file write attempts
    if re.search(r'(>|>>|Out-File|Set-Content|Add-Content|Tee-Object)', command_str, re.IGNORECASE):
        return False

    # Check for branch deletion
    if re.search(r'git\s+branch\s+.*(-D|-d|--delete)', command_str, re.IGNORECASE):
        return False

    # Split command by pipeline / chaining operators
    segments = re.split(r'&&|\|\||;|\|', command_str)
    safe_patterns = [
        r'^\s*git\s+(status|diff|log|branch|show)(\s+[^\n\r>|;&]+)?$',
        r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+-m\s+unittest(\s+[^\n\r>|;&]+)?$',
        r'^\s*node(\.exe)?\s+.*(tests[\\/]|--test)[^\n\r>|;&]*$',
        r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+-m\s+org_v5\.cli\s+(report|status|validate|events)(\s+[^\n\r>|;&]+)?$',
        r'^\s*(["\']?[^"\']*[\\/])?python(\.exe)?["\']?\s+\.agents[\\/]scripts[\\/]utf8_writer\.py(\s+[^\n\r>|;&]+)?$',
        r'^\s*where(\.exe)?\s+[a-zA-Z0-9_\-\.]+$',
        r'^\s*which\s+[a-zA-Z0-9_\-\.]+$'
    ]
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        matched = False
        for pattern in safe_patterns:
            if re.search(pattern, seg, re.IGNORECASE):
                matched = True
                break
        if not matched:
            return False
    return True

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

        # 1. Check STOP (Kill Switch) in workspace
        stop_file = workspace_root / ".agents" / "state" / "STOP"
        stop_exists = stop_file.exists()

        # 2. Check Run Phase (P0-02: phase is canonical in V5.2)
        run_is_escalated_or_paused = False
        curr_run_file = workspace_root / "runs" / "CURRENT"
        if curr_run_file.exists():
            try:
                run_id = curr_run_file.read_text(encoding="utf-8").strip()
                state_file = workspace_root / "runs" / run_id / "state.json"
                if state_file.exists():
                    st = json.loads(state_file.read_text(encoding="utf-8"))
                    # Canonical V5.2 phase check with legacy status fallback
                    phase = st.get("phase", st.get("status", ""))
                    if phase in ("ESCALATED", "PAUSED"):
                        run_is_escalated_or_paused = True
            except Exception:
                run_is_escalated_or_paused = True

        # Diagnostic exception under STOP or ESCALATED / PAUSED
        if stop_exists or run_is_escalated_or_paused:
            state_label = "STOP ativo" if stop_exists else "Run em ESCALATED/PAUSED"
            if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
                path_val = args.get("AbsolutePath", args.get("SearchPath", args.get("DirectoryPath", "")))
                if path_val and is_secret_path(path_val):
                    emit_decision("deny", f"{state_label}: leitura de segredo bloqueada")
                emit_decision("allow", f"{state_label}: leitura de diagnostico permitida")
            if tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if "utf8_writer.py" in cmd:
                    emit_decision("allow", f"{state_label}: registro de relatorio via utf8_writer permitido")
                if is_safe_inspection_command(cmd):
                    emit_decision("allow", f"{state_label}: inspecao permitida")
                emit_decision("deny", f"{state_label}: comando modificador bloqueado: {cmd}")
            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                target = str(args.get("TargetFile", ""))
                rel_target = get_relative_target(target, workspace_root)
                if rel_target.startswith("runs/") or rel_target.startswith("evidence/") or rel_target.startswith("logs/"):
                    emit_decision("allow", f"{state_label}: registro de evidencia/relatorio de parada permitido")
                emit_decision("deny", f"{state_label}: modificacao de arquivo bloqueada fora de evidencias: {rel_target}")
            if tool_name == "invoke_subagent":
                emit_decision("deny", f"{state_label}: novas delegacoes de subagente bloqueadas")
            emit_decision("deny", f"{state_label}: operacao {tool_name} bloqueada")

        # 3. Explicit Forbidden Tools
        if tool_name in ("define_subagent", "schedule"):
            emit_decision("deny", f"Ferramenta {tool_name} e estritamente proibida na organizacao V5.2")

        # 4. Delegation Check (P1-08)
        if tool_name == "invoke_subagent":
            emit_decision("allow", "Delegacao de subagente autorizada na politica de execucao")

        # 5. PROTECT_ORG Core Lock Check
        protect_org_file = workspace_root / ".agents" / "state" / "PROTECT_ORG"
        if protect_org_file.exists():
            target_path = ""
            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                target_path = str(args.get("TargetFile", ""))
            elif tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if re.search(r'(\.agents|org_v5|AGENTS\.md)', cmd) and re.search(r'(git\s+apply|Remove-Item|rm|del|Set-Content|Out-File|echo\s+.*>|>>)', cmd):
                    emit_decision("deny", "PROTECT_ORG ativo: modificacoes no Core (.agents, org_v5, AGENTS.md) exigem autorizacao humana explicita")
            if target_path:
                rel_target = get_relative_target(target_path, workspace_root)
                if rel_target.startswith(".agents/") or rel_target.startswith("org_v5/") or rel_target == "AGENTS.md":
                    emit_decision("deny", f"PROTECT_ORG ativo: modificacao em {rel_target} bloqueada sem desbloqueio humano previo")

        # 6. Secrets Scanning in Paths
        if tool_name in ("view_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
            path_val = str(args.get("TargetFile", args.get("AbsolutePath", "")))
            if is_secret_path(path_val):
                emit_decision("deny", f"Acesso a arquivo de segredos ou credenciais ({path_val}) bloqueado por politica de seguranca")

        # 7. Command Classification (run_command)
        if tool_name == "run_command":
            cmd = str(args.get("CommandLine", ""))

            # 7.1 Secret Dumping or Exposure in Terminal (P0-06: DENY DIRETO)
            if re.search(r'(cat|type|Get-Content|head|tail|more|less)\s+.*\.env(?!(\.example|\.sample|\.template))', cmd, re.IGNORECASE):
                emit_decision("deny", "Exibicao de arquivo .env no terminal bloqueada")
            if re.search(r'(cat|type|Get-Content|head|tail|more|less)\s+.*(\.key|\.pem|credentials.*\.json|id_rsa|id_ed25519)', cmd, re.IGNORECASE):
                emit_decision("deny", "Exibicao de chave ou credencial no terminal bloqueada")
            if re.search(r'(^|\s|;)(printenv|env)(\s|$)|(\$env:[a-zA-Z0-9_]*(TOKEN|KEY|SECRET|PASSWORD))', cmd, re.IGNORECASE):
                emit_decision("deny", "Dump de variaveis de ambiente ou segredos no terminal bloqueado")

            # 7.2 Catastrophic / Destructive commands
            if re.search(r'rm\s+-r[f]?\s+(/|~|\$HOME|C:\\|D:\\)|rd\s+/s\s+/q\s+[C-Z]:\\|del\s+/s\s+/q\s+[C-Z]:\\', cmd, re.IGNORECASE):
                emit_decision("deny", "Comando destrutivo catastrofico bloqueado")
            if re.search(r'rm\s+-r|Remove-Item\s+-Recurse|rd\s+/s|git\s+clean\s+-f|git\s+reset\s+--hard', cmd, re.IGNORECASE):
                emit_decision("force_ask", "Confirmacao exigida para comando com potencial destrutivo")

            # 7.3 Git Main / Master Branch Protections & Force Push
            if re.search(r'git\s+push\s+.*(--force|-f|--force-with-lease)', cmd, re.IGNORECASE):
                emit_decision("deny", "Push forcado (--force / --force-with-lease) estritamente proibido")
            if re.search(r'git\s+push\s+.*(origin\s+)?(main|master)(\s|$)', cmd, re.IGNORECASE):
                emit_decision("deny", "Push direto para main/master proibido: utilize feature branch e PR")
            if re.search(r'git\s+(merge|rebase)\s+.*(main|master)(\s|$)', cmd, re.IGNORECASE):
                emit_decision("deny", "Merge ou rebase direto em main/master proibido sem autorizacao de release")

            # 7.4 External Publishing / Deployment
            if re.search(r'^(gcloud|aws|az|kubectl|helm|terraform|pulumi|firebase|vercel|netlify|heroku|docker\s+push|npm\s+publish)', cmd.strip(), re.IGNORECASE):
                emit_decision("force_ask", "Deploy ou publicacao em nuvem requer confirmacao humana explicita")
            if re.search(r'git\s+push|gh\s+pr\s+merge', cmd, re.IGNORECASE):
                emit_decision("force_ask", "Publicacao externa Git requer confirmacao")

            # 7.5 Unauthorized Memory Writes
            if re.search(r'memanto\s+(remember|edit|forget|upload|migrate)|python\s+-m\s+org_v5\.cli\s+memory-write', cmd, re.IGNORECASE):
                emit_decision("deny", "Escrita em memoria fora da rota governada de promocao de core e proibida")

            # 7.6 Safe Inspection Commands
            if is_safe_inspection_command(cmd):
                emit_decision("allow", "Comando seguro de inspecao/testes aprovado")

            # Default for unclassified commands: ASK (P0-04: nunca allow)
            emit_decision("ask", f"Comando fora da faixa allow segura: confirmacao recomendada: {cmd[:100]}")

        # 8. Safe File Reading Operations
        if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
            path_val = args.get("AbsolutePath", args.get("SearchPath", args.get("DirectoryPath", "")))
            if path_val and is_secret_path(path_val):
                emit_decision("deny", f"Acesso a arquivo de segredos bloqueado: {path_val}")
            emit_decision("allow", "Operacao segura de leitura e inspecao")

        # 9. Standard File Modifications inside workspace
        if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
            target = str(args.get("TargetFile", ""))
            if not target:
                emit_decision("ask", "Arquivo de destino nao especificado")
            if not is_path_inside(target, workspace_root):
                emit_decision("deny", f"Modificacao fora dos limites do workspace bloqueada: {target}")
            emit_decision("allow", "Modificacao de arquivo dentro do workspace aprovada")

        # 10. Default fallback for unknown tools: ASK (P0-04)
        emit_decision("ask", f"Ferramenta desconhecida ou nao classificada ({tool_name}): requer confirmacao")

    except Exception as e:
        emit_decision("deny", f"Falha interna do pretool_guard: {str(e)}")

if __name__ == "__main__":
    main()
