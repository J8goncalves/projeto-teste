import sys
import json
import os
import re
import sqlite3
from pathlib import Path

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

def get_actionable_pending_reviews(workspace_root, run_id):
    """
    Deriva pendencias reais a partir do contrato canonico de org_v5/control.py.
    Verifica artifacts submetidos sem review ACCEPT, e valida se o estado permite continuidade.
    """
    state_file = workspace_root / "runs" / run_id / "state.json"
    if not state_file.exists():
        return []
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        phase = st.get("phase", st.get("status", ""))
        # Estados terminais ou de escalonamento nao permitem progresso acionavel
        if phase in ("ESCALATED", "PAUSED", "CLOSED"):
            return []

        artifacts = st.get("artifacts", {})
        accepted = st.get("accepted", {})

        pending = []
        for art_id in artifacts.keys():
            if art_id not in accepted:
                pending.append(art_id)
        return pending
    except Exception:
        return []

def record_and_check_attempt(workspace_root, run_id, conv_id):
    """
    Persistencia atomica e transacional via SQLite para contagem de tentativas
    por (run_id, conv_id) sem perda de atualizacao por corrida e sem colisao de IDs por truncamento (F08).
    Retorna o numero de tentativas registradas nesta transacao.
    """
    state_dir = workspace_root / ".agents" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "stop_attempts.db"

    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=15.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stop_attempts (
                run_id TEXT NOT NULL,
                conv_id TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                PRIMARY KEY (run_id, conv_id)
            )
        """)
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur = conn.cursor()
            cur.execute("SELECT attempts FROM stop_attempts WHERE run_id = ? AND conv_id = ?", (run_id, conv_id))
            row = cur.fetchone()
            current = row[0] if row else 0
            new_attempts = current + 1
            if row:
                cur.execute("UPDATE stop_attempts SET attempts = ? WHERE run_id = ? AND conv_id = ?", (new_attempts, run_id, conv_id))
            else:
                cur.execute("INSERT INTO stop_attempts (run_id, conv_id, attempts) VALUES (?, ?, ?)", (run_id, conv_id, new_attempts))
            conn.execute("COMMIT")
            return new_attempts
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()

def clear_attempt(workspace_root, run_id, conv_id):
    """
    Remove o registro de tentativas da chave (run_id, conv_id) ao finalizar ou esgotar limites.
    """
    state_dir = workspace_root / ".agents" / "state"
    db_path = state_dir / "stop_attempts.db"
    if not db_path.exists():
        return
    try:
        conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=15.0)
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("DELETE FROM stop_attempts WHERE run_id = ? AND conv_id = ?", (run_id, conv_id))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
        finally:
            conn.close()
    except Exception:
        pass

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
        workspace_root = resolve_workspace_root(data)

        term_reason = data.get("terminationReason", "")
        error_msg = data.get("error", "")
        fully_idle = data.get("fullyIdle", True)
        conv_id = data.get("conversationId", "default")

        # 1. Se o termino foi por erro, STOP ou condicao fatal, sempre autorizar termino imediato
        if term_reason in ("error", "max_steps_exceeded") or error_msg or not fully_idle:
            print(json.dumps({"decision": "terminate", "reason": f"Termino autorizado por condicao de parada: {term_reason}"}))
            return

        stop_file = workspace_root / ".agents" / "state" / "STOP"
        if stop_file.exists():
            print(json.dumps({"decision": "terminate", "reason": "STOP ativo, encerramento permitido"}))
            return

        # 2. Obter run_id atual
        curr_run_file = workspace_root / "runs" / "CURRENT"
        current_run_id = "no_run"
        if curr_run_file.exists():
            try:
                current_run_id = curr_run_file.read_text(encoding="utf-8").strip() or "no_run"
            except Exception:
                current_run_id = "no_run"

        # 3. Derivar pendencias reais do modelo canonico de org_v5/control.py (R08)
        actionable_pending = get_actionable_pending_reviews(workspace_root, current_run_id) if current_run_id != "no_run" else []

        # 4. Controle transacional atomico sem colisao ou corrida (F08)
        if actionable_pending:
            attempts = record_and_check_attempt(workspace_root, current_run_id, conv_id)
            if attempts <= 2:
                pending_desc = ", ".join(actionable_pending[:3])
                print(json.dumps({
                    "decision": "continue",
                    "reason": f"Pendencia acionavel detectada no modelo canonico ({pending_desc}). Tentativa {attempts}/2."
                }))
                return

        # Permitir encerramento e limpar estado da chave desta execucao
        clear_attempt(workspace_root, current_run_id, conv_id)
        print(json.dumps({"decision": "terminate", "reason": "Sem pendencias verificaveis ou limite de tentativas atingido."}))

    except Exception as e:
        print(json.dumps({"decision": "terminate", "reason": f"Erro interno stop_guard: {str(e)}"}))

if __name__ == "__main__":
    main()
