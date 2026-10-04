import argparse
import json
import os
import re
import sys

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def validate(tipo, arquivo, nivel):
    if not os.path.exists(arquivo):
        print(f"ERRO: Arquivo {arquivo} nao existe.")
        sys.exit(1)
        
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"ERRO: Arquivo {arquivo} não é UTF-8 válido.")
        sys.exit(1)
        
    if os.path.basename(arquivo).startswith("_TEMPLATE"):
        print("OK (arquivo template ignorado)")
        sys.exit(0)
        
    root = get_workspace_root()
    schema_file = os.path.join(root, '.agents', 'schemas', 'artifacts.json')
    if not os.path.exists(schema_file):
        print("AVISO: artifacts.json não encontrado.")
        sys.exit(0)
        
    with open(schema_file, 'r', encoding='utf-8') as f:
        schemas = json.load(f)
        
    artifacts = schemas.get("artefatos", {})
    
    tipo_key = f"`{tipo}`"
    if tipo_key not in artifacts:
        tipo_key = tipo
        
    schema = artifacts.get(tipo_key)
    if not schema:
        print(f"AVISO: Schema para tipo '{tipo}' não definido.")
        sys.exit(0)
        
    erros = []
    
    secoes = schema.get("secoes", [])
    if nivel == 3:
        secoes += schema.get("secoes_nivel3", [])
        
    for s in secoes:
        if not re.search(r'#+\s*' + re.escape(s), content, re.IGNORECASE):
            erros.append(f"Seção ausente: {s}")
            
    refs = schema.get("referencias", [])
    for r in refs:
        if "marcador de resultado obrigatório" in r.lower():
            if not re.search(r'Resultado:', content, re.IGNORECASE):
                erros.append("Marcador 'Resultado:' ausente.")
                
    if schema.get("marcador_resultado"):
        if not re.search(r'Resultado:', content, re.IGNORECASE):
            erros.append("Marcador 'Resultado:' ausente.")
            
    placeholders = [r'TBD', r'TODO', r'XXX', r'<preencher>', r'\[AAAA-MM-DD\]', r'\[Nome .*?\]']
    for p in placeholders:
        if re.search(p, content):
            erros.append(f"Placeholder não preenchido encontrado: {p}")
            
    if 'test-report' in tipo and re.search(r'FAIL', content):
        req_fail = ["Passos de reprodução", "Impacto", "Remediação sugerida"]
        for rf in req_fail:
            if not re.search(re.escape(rf), content, re.IGNORECASE):
                erros.append(f"Relatório de erro exige: {rf}")
                
    if erros:
        for e in erros:
            print(f"ERRO: {e}")
        sys.exit(1)
        
    print("OK")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tipo')
    parser.add_argument('arquivo')
    parser.add_argument('--nivel', type=int, default=1)
    args = parser.parse_args()
    
    validate(args.tipo, args.arquivo, args.nivel)

if __name__ == '__main__':
    main()
