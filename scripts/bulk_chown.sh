#!/usr/bin/env sh

HOST_UID=${HOST_UID:-1234}
HOST_GID=${HOST_GID:-1234}

USER_GROUP="${HOST_UID}:${HOST_GID}"

DIRS="./temp ./user_configs /var/www/html"

for DIR in $DIRS; do
  if [ -d "$DIR" ]; then
    echo "Changing owner of '$DIR' to $USER_GROUP ..."
    sudo chown -R "$USER_GROUP" "$DIR"
  else
    echo "Warning: '$DIR' is not a valid directory. Skipping."
  fi
done

echo "All done."