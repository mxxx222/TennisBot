# GitHub OAuth App Workflow Setup

Jos `git push` epäonnistuu workflow scope -ongelman takia, seuraa näitä ohjeita:

## 1. Päivitä OAuth App Permissions

1. Mene GitHubiin: https://github.com/settings/developers
2. Valitse OAuth App jota käytät (`gh` CLI:lle)
3. Klikkaa **"Edit"**
4. Valitse **"Expires: No expiration"** (jos ei ole jo valittu)
5. Lisää **workflow** scope:
   - **Repository permissions:**
     - **Actions:** Read and write
     - **Contents:** Read and write
     - **Metadata:** Read (automatic)
   - **Account permissions:**
     - **Workflow:** Read and write
6. Klikkaa **"Update application"**
7. Kirjaudu uudelleen `gh` CLI:llä:
   ```bash
   gh auth refresh -s workflow
   ```

## 2. Vaihtoehto: Käytä GitHub Personal Access Token

Jos OAuth App ei toimi, voit käyttää Personal Access Tokenia:

1. Luo token: https://github.com/settings/tokens
2. Valitse scopes:
   - `repo` (full control)
   - `workflow` (write access)
3. Aseta token ympäristömuuttujaksi:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```
4. TAI aseta se GitHub CLI:lle:
   ```bash
   gh auth login --with-token < your_token.txt
   ```

## 3. Tarkista Workflow Permissions

Jos workflow-epäonnistuu push-vaiheessa, tarkista että workflow-tiedostossa on oikeat permissions:

```yaml
permissions:
  contents: write
  actions: write
```

Tämä lisätään workflow-tiedoston `jobs`-osion alle.

## 4. Testaa Push

Kun olet päivittänyt permissions:

```bash
# Tarkista auth status
gh auth status

# Testaa push
git push
```

Jos ongelma jatkuu, tarkista:
- `gh auth refresh -s workflow`
- `gh auth status` (pitäisi näyttää workflow scope)

