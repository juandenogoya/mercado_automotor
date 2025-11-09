"""
Genera certificado SSL auto-firmado para desarrollo local.
Usado por mercadolibre_oauth.py para servidor HTTPS de callback.
"""

from pathlib import Path
import subprocess
import sys


def create_self_signed_cert(cert_dir: Path = None) -> tuple[Path, Path]:
    """
    Crea certificado SSL auto-firmado para localhost.

    Returns:
        Tupla (cert_file, key_file)
    """
    if cert_dir is None:
        cert_dir = Path(__file__).parent

    cert_file = cert_dir / "localhost.crt"
    key_file = cert_dir / "localhost.key"

    # Si ya existen, usarlos
    if cert_file.exists() and key_file.exists():
        return cert_file, key_file

    try:
        # Generar certificado usando OpenSSL
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-nodes",
            "-subj", "/CN=localhost"
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        print(f"✅ Certificado SSL creado: {cert_file}")
        print(f"✅ Clave privada creada: {key_file}")

        return cert_file, key_file

    except FileNotFoundError:
        print("❌ OpenSSL no encontrado. Instalando alternativa...")
        return create_cert_with_cryptography(cert_dir)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando certificado: {e}")
        return create_cert_with_cryptography(cert_dir)


def create_cert_with_cryptography(cert_dir: Path) -> tuple[Path, Path]:
    """
    Crea certificado usando la librería cryptography (no requiere OpenSSL).
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from datetime import datetime, timedelta

        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Crear certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                ]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Guardar archivos
        cert_file = cert_dir / "localhost.crt"
        key_file = cert_dir / "localhost.key"

        # Escribir certificado
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Escribir clave privada
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        print(f"✅ Certificado SSL creado con cryptography: {cert_file}")

        return cert_file, key_file

    except ImportError:
        print("❌ cryptography no está instalada")
        print("Instalá con: pip install cryptography")
        sys.exit(1)


if __name__ == "__main__":
    cert, key = create_cert_with_cryptography(Path(__file__).parent)
    print(f"\nCertificado: {cert}")
    print(f"Clave: {key}")
