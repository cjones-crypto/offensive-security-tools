#!/bin/bash

TARGET="<ip address>"
USER="<username>"
PASS="<passowrd>"

echo "[+] Enumerating SMB shares on $TARGET"
echo

# Pull share list
SHARES=$(smbclient -U "$USER%$PASS" -L //$TARGET 2>/dev/null | awk '/Disk/ {print $1}')

echo "[+] Shares found:"
echo "$SHARES"
echo

for SHARE in $SHARES; do
    echo "------------------------------------------------------------"
    echo "[+] Testing access to: $SHARE"
    echo "------------------------------------------------------------"

    # Try listing the share
    smbclient //$TARGET/$SHARE -U "$USER%$PASS" -c "ls" 2>/dev/null

    # If listing works, offer interactive shell
    if [ $? -eq 0 ]; then
        echo
        echo "[+] Access confirmed on $SHARE"
        echo "[+] Opening interactive smbclient shell..."
        echo
        smbclient //$TARGET/$SHARE -U "$USER%$PASS"
    else
        echo "[-] No access to $SHARE"
    fi

    echo
done
