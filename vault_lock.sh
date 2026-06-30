#!/usr/bin/env bash
# =============================================================================
# G.O.D. STACK VAULT LOCK ENGINE v1.1.0 (vault_lock.sh)
# Architecture: Automated Ephemeral Storage Archival & Rotation
# =============================================================================

echo -e "\033[1;34m[VAULT-CORE] Initializing secure data exfiltration matrix...\033[0m"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="vaults/god_stack_backup_$TIMESTAMP.tar.gz"

# Ensure target directories exist before archiving
mkdir -p vaults outputs storage
touch storage/storage.sqlite 2>/dev/null # Ensure mock file exists for testing

echo -e "\033[1;35m[VAULT-CORE] Compressing storage.sqlite and raw outputs...\033[0m"

# Compress without preserving full absolute paths
tar -czf "$BACKUP_NAME" storage/ outputs/ 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "\033[1;32m[PERFECT] Data securely archived to $BACKUP_NAME\033[0m"
else
    echo -e "\033[1;31m[CRITICAL] Compression fault detected during archival.\033[0m"
    exit 1
fi

# Rotate old backups - keep only the 5 most recent
echo -e "\033[1;36m[VAULT-CORE] Enforcing FOSS compliance retention policy (Max: 5)...\033[0m"
ls -tp vaults/god_stack_backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -I {} rm -f -- {}

echo -e "\033[1;32m[SUCCESS] Vault lifecycle complete. Data is locked.\033[0m"
exit 0
