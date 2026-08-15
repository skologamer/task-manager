<#
Creates a GitHub repository for the current folder and pushes the code.

Usage (PowerShell):

# Option A: Using GitHub CLI (recommended if authenticated):
#   Install gh: https://cli.github.com/
#   gh auth login
#   ./scripts/create_github_repo.ps1 -RepoName "owner/repo" -Private:$false

# Option B: Using a Personal Access Token in env var GITHUB_TOKEN:
#   $env:GITHUB_TOKEN = 'ghp_...'
#   ./scripts/create_github_repo.ps1 -RepoName "owner/repo" -Private:$true

# The script will attempt to initialize a git repo, create the remote, and push.
# It requires `git` to be installed locally.
# See comments in script for details.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoName,
    [bool]$Private = $true
)

function Fail($msg){ Write-Error $msg; exit 1 }

Write-Host "Creating GitHub repo: $RepoName (private=$Private)"

# Check git
$git = Get-Command git -ErrorAction SilentlyContinue
if(-not $git){ Fail 'git is not installed or not on PATH. Install Git first: https://git-scm.com/downloads' }

# If not inside a git repo, init
if(-not (git rev-parse --is-inside-work-tree 2>$null)){
    git init
    Write-Host 'Initialized local git repository.'
}

# Stage and commit
git add --all
if(-not (git status --porcelain)){
    Write-Host 'No changes to commit.'
} else {
    git commit -m "Initial commit"
    Write-Host 'Created initial commit.'
}

# Create remote via gh if available
$gh = Get-Command gh -ErrorAction SilentlyContinue
if($gh){
    Write-Host 'Using gh CLI to create repo...'
    gh repo create $RepoName --$([string]::Join('', ($Private ? 'private' : 'public'))) --source=. --remote=origin --push
    Write-Host 'Repo created and pushed via gh.'
    exit 0
}

# Fallback to GitHub API using GITHUB_TOKEN
if(-not $env:GITHUB_TOKEN){
    Fail 'Neither gh CLI found nor GITHUB_TOKEN set. Install gh or set GITHUB_TOKEN environment variable.'
}

$parts = $RepoName.Split('/')
if($parts.Length -ne 2){ Fail 'RepoName must be in owner/repo format.' }
$owner = $parts[0]; $repo = $parts[1]

$body = @{ name = $repo; private = $Private } | ConvertTo-Json
$url = "https://api.github.com/orgs/$owner/repos"

try{
    # Try creating under owner as an org first
    $resp = Invoke-RestMethod -Method Post -Uri $url -Body $body -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'create-github-repo-script' }
    Write-Host "Created repo under org $owner"
} catch {
    # If that fails, try creating under the authenticated user
    $url2 = "https://api.github.com/user/repos"
    $resp2 = Invoke-RestMethod -Method Post -Uri $url2 -Body $body -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'create-github-repo-script' }
    Write-Host "Created repo under your user account"
}

# Add remote and push
$remoteUrl = "https://github.com/$RepoName.git"
git remote remove origin 2>$null | Out-Null
git remote add origin $remoteUrl
git branch -M main 2>$null
git push -u origin main
Write-Host 'Pushed to remote origin/main.'
