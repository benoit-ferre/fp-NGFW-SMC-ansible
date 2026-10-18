# Ansible lint addition

Copy the files from this overlay to the repository root after applying the
previous Python lint bundle. Append the contents of `gitignore-additions.txt`
to `.gitignore`.

Run the checks with:

```bash
python -m pip install -r requirements-lint.txt
make lint-ansible
```

The initial configuration deliberately uses the strict `production` profile.
Review the first findings before adding any exclusions or skipped rules.
