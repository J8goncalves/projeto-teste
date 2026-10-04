# Permissões do Antigravity

Estas permissões devem ser aplicadas nas Configurações do Antigravity (fase F9).
Para macOS e Linux: Configurações -> Customizations -> Permissions.
CLI: ~/.gemini/antigravity-cli/settings.json.
Para Windows: O sistema anterior é usado, então registre que os padrões command(...) podem exigir 
egex:.

`json
{
  "permissions": {
    "deny": [
      "command(sudo)",
      "command(rm -rf)",
      "command(regex:curl .*\\|\\s*(sh|bash))",
      "command(regex:wget .*\\|\\s*(sh|bash))",
      "command(memanto remember)",
      "command(memanto edit)",
      "command(memanto forget)",
      "command(memanto upload)",
      "command(memanto migrate)",
      "command(memanto connect)",
      "command(memanto serve)",
      "command(memanto ui)",
      "command(memanto schedule)",
      "command(memanto policy)",
      "command(memanto memory)",
      "command(memanto agent)",
      "command(memanto answer)",
      "command(memanto recall)",
      "command(memanto daily-summary)",
      "command(memanto detect-conflicts)",
      "command(memanto conflicts)",
      "write_file(.git/)",
      "read_file(.env)",
      "write_file(.env)"
    ],
    "ask": [
      "command(git push)",
      "command(git merge)",
      "command(git rebase)",
      "command(git reset)",
      "command(docker push)",
      "command(npm publish)",
      "command(npx)",
      "command(npm install)",
      "command(yarn add)",
      "command(pnpm add)",
      "command(pip install)",
      "command(cargo add)",
      "command(gcloud)",
      "command(aws)",
      "command(az)",
      "command(kubectl)",
      "command(helm)",
      "command(terraform)",
      "command(firebase)",
      "command(vercel)",
      "command(netlify)",
      "command(gh release)",
      "command(gh pr merge)"
    ],
    "allow": [
      "command(git status)",
      "command(git diff)",
      "command(git log)",
      "command(git branch)",
      "command(git add)",
      "command(git commit)",
      "command(memanto --version)",
      "command(memanto status)",
      "command(memanto config show)"
    ]
  }
}
`
