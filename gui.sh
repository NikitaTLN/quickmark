export SSL_CERT_FILE="/nix/store/603anldknrz5cf82w6hf8am26s0mhyrr-etc/etc/ssl/certs/ca-bundle.crt"
export LD_LIBRARY_PATH="/nix/store/sg0rg4f0hzm0vhfxys0xiiyd0gspy39c-gtk+3-3.24.49/lib:$LD_LIBRARY_PATH"
uv run python gui.py
