import sys
import json
import os
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
os.chdir(workspace_root)

def emit_decision(decision, reason, tool_name=""):
    out = {"decision": decision, "reason": reason}
    print(json.dumps(out))
    sys.exit(0)

def is_safe_inspection_command(command_str):
    # Split command by operators &&, ||, ;, |
    segments = re.split(r'&&|\|\||;|\|', command_str)
    safe_prefixes = [
        r'^\s*git\s+(status|diff|log|branch|show)',
        r'^\s*(\.?\\?\.venv\\Scripts\\python(\.exe)?|node)\s+.*(unittest|--test|test_)',
        r'^\s*(\.?\\?\.venv\\Scripts\\python(\.exe)?)\s+-m\s+org_v5\.cli\s+(report|status|validate|events)',
        r'^\s*(\.?\\?\.venv\\Scripts\\python(\.exe)?)\s+\.agents[\\/]scripts[\\/]utf8_writer\.py',
        r'^\s*echo\s+',
        r'^\s*dir\s*',
        r'^\s*Get-ChildItem\s*',
        r'^\s*Select-Object\s*',
        r'^\s*where\s+',
        r'^\s*which\s+'
    ]
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        matched = False
        for pattern in safe_prefixes:
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
            emit_decision("allow", "Empty input")

        data = json.loads(raw_input)
        tool_call = data.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        conversation_id = data.get("conversationId", "default")

        # 1. Check STOP / Kill Switch
        stop_exists = os.path.exists(".agents/state/STOP")

        # 2. Check Run State (ESCALATED / PAUSED)
        current_run_id = None
        run_is_paused_or_escalated = False
        if os.path.exists("runs/CURRENT"):
            with open("runs/CURRENT", "r", encoding="utf-8") as f:
                current_run_id = f.read().strip()
        if current_run_id and os.path.exists(f"runs/{current_run_id}/state.json"):
            try:
                with open(f"runs/{current_run_id}/state.json", "r", encoding="utf-8") as f:
                    state_obj = json.load(f)
                    status = state_obj.get("status", "")
                    if status in ("ESCALATED", "PAUSED"):
                        run_is_paused_or_escalated = True
            except Exception:
                pass

        # Diagnostic exception under STOP / ESCALATED:
        # Allow read-only tools and utf8_writer / evidence recording
        if stop_exists or run_is_paused_or_escalated:
            state_label = "STOP ativo" if stop_exists else "Run ESCALATED/PAUSED"
            if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
                emit_decision("allow", f"{state_label}: leitura permitida para diagnostico")
            if tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if "utf8_writer.py" in cmd:
                    emit_decision("allow", f"{state_label}: registro de relatorio de parada permitido via utf8_writer")
                if is_safe_inspection_command(cmd):
                    emit_decision("allow", f"{state_label}: comando de inspecao permitido")
                emit_decision("deny", f"{state_label}: comando modificador bloqueado: {cmd}")
            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                target = str(args.get("TargetFile", "")).replace('\\', '/')
                if target.startswith("runs/") or target.startswith("evidence/") or target.startswith("logs/"):
                    emit_decision("allow", f"{state_label}: registro de relatorio de parada permitido em pasta de evidencias")
                emit_decision("deny", f"{state_label}: escrita bloqueada fora de evidencias: {target}")
            emit_decision("deny", f"{state_label}: acao {tool_name} bloqueada")

        # 3. Explicit Forbidden Tools
        if tool_name in ("define_subagent", "schedule"):
            emit_decision("deny", f"Ferramenta {tool_name} e estritamente proibida na organizacao V5.2")

        # 4. PROTECT_ORG Core Lock Check
        protect_org_exists = os.path.exists(".agents/state/PROTECT_ORG")
        if protect_org_exists:
            target_path = ""
            if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                target_path = str(args.get("TargetFile", "")).replace('\\', '/')
            elif tool_name == "run_command":
                cmd = str(args.get("CommandLine", ""))
                if re.search(r'(\.agents|org_v5|AGENTS\.md)', cmd) and re.search(r'(git\s+apply|Remove-Item|rm|del|Set-Content|Out-File|echo\s+.*>)', cmd):
                    emit_decision("deny", "PROTECT_ORG ativo: modificacoes no Core (.agents, org_v5, AGENTS.md) exigem autorizacao humana explicita")
            if target_path:
                rel = os.path.relpath(os.path.abspath(target_path), workspace_root).replace('\\', '/')
                if rel.startswith(".agents/") or rel.startswith("org_v5/") or rel == "AGENTS.md":
                    emit_decision("deny", f"PROTECT_ORG ativo: modificacao em {rel} bloqueada sem desbloqueio humano previo")

        # 5. Secrets Scanning in Paths
        if tool_name in ("view_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
            path_val = str(args.get("TargetFile", args.get("AbsolutePath", ""))).replace('\\', '/')
            # Block real secrets (.env except .env.example, .key, .pem, .p12, credentials.json, id_rsa)
            if re.search(r'(^|[\\\\/])(\.env(?!(\.example|\.sample|\.template))|.*\.pem$|.*\.key$|.*\.p12$|.*\.pfx$|id_rsa.*|id_ed25519.*|credentials.*\.json$|\.npmrc$|\.pypirc$|.*\.tfstate$)', path_val, re.IGNORECASE):
                emit_decision("deny", f"Acesso a arquivo de segredos ou credenciais ({path_val}) bloqueado por politica de seguranca")

        # 6. Command Classification (run_command)
        if tool_name == "run_command":
            cmd = str(args.get("CommandLine", ""))
            
            # 6.1 Catastrophic / Destructive commands
            if re.search(r'rm\s+-r[f]?\s+(/|~|\$HOME|C:\\|D:\\)|rd\s+/s\s+/q\s+[C-Z]:\\|del\s+/s\s+/q\s+[C-Z]:\\', cmd, re.IGNORECASE):
                emit_decision("deny", "Comando destrutivo catastrofico bloqueado")
            if re.search(r'rm\s+-r|Remove-Item\s+-Recurse|rd\s+/s|git\s+clean\s+-f|git\s+reset\s+--hard', cmd, re.IGNORECASE):
                emit_decision("force_ask", "Confirmacao exigida para comando com potencial destrutivo")

            # 6.2 Git Main / Master Branch Protections & Force Push
            if re.search(r'git\s+push\s+.*(--force|-f|--force-with-lease)', cmd, re.IGNORECASE):
                emit_decision("deny", "Push forcado (--force / --force-with-lease) estritamente proibido")
            if re.search(r'git\s+push\s+.*(origin\s+)?(main|master)', cmd, re.IGNORECASE):
                emit_decision("deny", "Push direto para main/master proibido: utilize feature branch e PR")
            if re.search(r'git\s+(merge|rebase)\s+.*(main|master)', cmd, re.IGNORECASE):
                emit_decision("deny", "Merge ou rebase direto em main/master proibido sem autorizacao de release")

            # 6.3 External Publishing / Deployment
            if re.search(r'^(gcloud|aws|az|kubectl|helm|terraform|pulumi|firebase|vercel|netlify|heroku|docker\s+push|npm\s+publish)', cmd.strip(), re.IGNORECASE):
                emit_decision("force_ask", "Deploy ou publicacao em nuvem requer confirmacao humana explicita")
            if re.search(r'git\s+push|gh\s+pr\s+merge', cmd, re.IGNORECASE):
                emit_decision("force_ask", "Publicacao externa Git requer confirmacao")

            # 6.4 Unauthorized Memory Writes
            if re.search(r'memanto\s+(remember|edit|forget|upload|migrate)|python\s+-m\s+org_v5\.cli\s+memory-write', cmd, re.IGNORECASE):
                emit_decision("deny", "Escrita em memoria fora da rota governada de promocao de core e proibida")

            # 6.5 Safe Inspection Commands
            if is_safe_inspection_command(cmd):
                emit_decision("allow", "Comando seguro de inspecao/testes aprovado")

            # Default for unclassified commands
            emit_decision("ask", "Comando fora da faixa allow padrao: confirmacao recomendada")

        # 7. Safe File Operations (view_file / list_dir / grep_search)
        if tool_name in ("view_file", "list_dir", "grep_search", "find_by_name"):
            emit_decision("allow", "Operacao segura de leitura e inspecao")

        # 8. Standard File Modifications inside workspace
        if tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
            target = str(args.get("TargetFile", "")).replace('\\', '/')
            abs_target = os.path.abspath(target)
            if abs_target.startswith(os.path.abspath(workspace_root)):
                emit_decision("allow", "Modificacao de arquivo dentro do workspace aprovada")
            else:
                emit_decision("deny", "Modificacao fora dos limites do workspace bloqueada")

        # Default fallback
        emit_decision("allow", "Acao autorizada por padrao de governanca sandbox")

    except Exception as e:
        # Fail-closed internally: if guard script catches error, block rather than fail-open
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"pretool_guard exception: {str(e)}\n")
        emit_decision("deny", f"Falha interna do pretool_guard: {str(e)}")

if __name__ == "__main__":
    main()
