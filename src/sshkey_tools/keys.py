from typing import Union
from cryptography.hazmat.primitives import (
    serialization as _SERIALIZATION,
    hashes as _HASHES
)
from cryptography.hazmat.primitives.asymmetric import (
    rsa as _RSA,
    dsa as _DSA,
    ec as _ECDSA,
    ed25519 as _ED25519,
    padding as _PADDING
)

from .exceptions import (
    InvalidCurveException,
    InvalidKeyException,
    InvalidHashException
)


PUBKEY_MAP = {
    _RSA.RSAPublicKey: "RSAPublicKey",
    _DSA.DSAPublicKey: "DSAPublicKey",
    _ECDSA.EllipticCurvePublicKey: "ECDSAPublicKey",
    _ED25519.Ed25519PublicKey: "ED25519PublicKey"
}

PRIVKEY_MAP = {
    _RSA.RSAPrivateKey: "RSAPrivateKey",
    _DSA.DSAPrivateKey: "DSAPrivateKey",
    _ECDSA.EllipticCurvePrivateKey: "ECDSAPrivateKey",
    _ED25519.Ed25519PrivateKey: "ED25519PrivateKey"
}

STR_OR_BYTES = Union[str, bytes]


# Only valid in Py3.11+
# PUBKEY_CLASSES = Union[*PUBKEY_MAP.keys()]
# PRIVKEY_CLASSES = Union[*PRIVKEY_MAP.keys()]

PUBKEY_CLASSES = Union[
    _RSA.RSAPublicKey,
    _DSA.DSAPublicKey,
    _ECDSA.EllipticCurvePublicKey,
    _ED25519.Ed25519PublicKey
]

PRIVKEY_CLASSES = Union[
    _RSA.RSAPrivateKey,
    _DSA.DSAPrivateKey,
    _ECDSA.EllipticCurvePrivateKey,
    _ED25519.Ed25519PrivateKey
]

CURVE_OR_STRING = Union[str, _ECDSA.EllipticCurve]
ECDSA_CURVES = {
    'secp256r1': _ECDSA.SECP256R1,
    'secp384r1': _ECDSA.SECP384R1,
    'secp521r1': _ECDSA.SECP521R1,
}

RSA_SIGNATURE_HASHES = {
    'sha1': _HASHES.SHA1,
    'sha256': _HASHES.SHA256,
    'sha512': _HASHES.SHA512
}


class PublicKey:
    def __init__(self, *args, **kwargs):
        self.key = kwargs.get('key', None)
        self.public_numbers = kwargs.get('public_numbers', None)
        self.comment = kwargs.get('comment', None)
        self.key_type = kwargs.get('key_type', None)
        self.export_opts = {
            "pub_encoding": _SERIALIZATION.Encoding.OpenSSH,
            "pub_format": _SERIALIZATION.PublicFormat.OpenSSH,
        }


    @classmethod
    def from_class(
        cls,
        key_class: PUBKEY_CLASSES,
        comment: STR_OR_BYTES = None,
        key_type: STR_OR_BYTES = None
    ):
        for key in PUBKEY_MAP.keys():
            if isinstance(key_class, key):
                return globals()[PUBKEY_MAP[key]](
                    key=key_class,
                    comment=comment,
                    key_type=key_type
                )

        raise InvalidKeyException("Invalid public key")

    @classmethod
    def from_string(cls, data: STR_OR_BYTES) -> 'PublicKey':
        if isinstance(data, str):
            data = data.encode('utf-8')

        split = data.split(b' ')
        comment = ''
        if len(split) > 1:
            key_type = split[0]

            if len(split) > 2:
                comment = split[2]


        public_key = _SERIALIZATION.load_ssh_public_key(data)

        return cls.from_class(public_key, comment, key_type)


    @classmethod
    def from_file(cls, file_name: str) -> 'PublicKey':
        with open(file_name, 'rb') as f:
            data = f.read()

        return cls.from_string(data)

    def to_bytes(self) -> bytes:
        return self.key.public_bytes(
            self.export_opts['pub_encoding'],
            self.export_opts['pub_format'],
        )

    def to_string(self) -> str:
        public_bytes = self.to_bytes()

        if self.comment is not None:
            public_bytes += b' ' + self.comment

        return public_bytes.decode('utf-8')

    def to_file(self, filename: str):
        with open(filename, 'w') as pubkey_file:
            pubkey_file.write(self.to_string())

class PrivateKey:
    def __init__(self, *args, **kwargs):
        self.key = kwargs.get('key', None)
        self.public_key = kwargs.get('public_key', None)
        self.private_numbers = kwargs.get('private_numbers', None)
        self.export_opts = {
            "encoding": _SERIALIZATION.Encoding.PEM,
            "format": _SERIALIZATION.PrivateFormat.OpenSSH,
            "encryption": _SERIALIZATION.BestAvailableEncryption,
        }

    @classmethod
    def from_class(cls, key_class: PRIVKEY_CLASSES):
        for key in PRIVKEY_MAP.keys():
            if isinstance(key_class, key):
                return globals()[PRIVKEY_MAP[key]](key=key_class)

        raise InvalidKeyException("Invalid private key")

    @classmethod
    def from_string(cls, data: STR_OR_BYTES, password: str = None) -> 'PrivateKey':
        if isinstance(data, str):
            data = data.encode('utf-8')

        private_key = _SERIALIZATION.load_ssh_private_key(
                data,
                password=password
        )

        return cls.from_class(private_key)

    @classmethod
    def from_file(cls, filename: str, password: str = None) -> 'PrivateKey':
        with open(filename, 'rb') as key_file:
            return cls.from_string(key_file.read(), password)

    def to_bytes(self, password: STR_OR_BYTES = None) -> bytes:
        if isinstance(password, str):
            password = password.encode('utf-8')

        encryption = _SERIALIZATION.NoEncryption()
        if password is not None:
            encryption = self.export_opts['encryption'](password)

        return self.key.private_bytes(
            self.export_opts['encoding'],
            self.export_opts['format'],
            encryption
        )

    def to_string(self, password: STR_OR_BYTES = None, encoding: str = 'utf-8') -> str:
        return self.to_bytes(password).decode(encoding)

    def to_file(self, filename: str, password: STR_OR_BYTES = None) -> None:
        with open(filename, 'wb') as key_file:
            key_file.write(
                self.to_bytes(
                    password
                )
            )

class RSAPublicKey(PublicKey):
    def __init__(
        self,
        key: _RSA.RSAPublicKey,
        comment: STR_OR_BYTES = None,
        key_type: STR_OR_BYTES = None
    ):
        super().__init__(
            key=key,
            comment=comment,
            key_type=key_type,
            public_numbers=key.public_numbers(),
        )

    @classmethod
    def from_numbers(cls, e: int, n: int):
        return cls(
            key=_RSA.RSAPublicNumbers(e, n).public_key()
        )

class RSAPrivateKey(PrivateKey):
    def __init__(self, key: _RSA.RSAPrivateKey):
        super().__init__(
            key=key,
            public_key=RSAPublicKey(
                key.public_key()
            ),
            private_numbers=key.private_numbers()
        )

    @classmethod
    def from_numbers(
        cls,
        n: int,
        e: int,
        d: int,
        p: int = None,
        q: int = None,
        dmp1: int = None,
        dmq1: int = None,
        iqmp: int = None
    ):
        if None in (p, q):
            p, q = _RSA.rsa_recover_prime_factors(n, e, d)

        dmp1 = _RSA.rsa_crt_dmp1(d, p) if dmp1 is None else dmp1
        dmq1 = _RSA.rsa_crt_dmq1(d, q) if dmq1 is None else dmq1
        iqmp = _RSA.rsa_crt_iqmp(p, q) if iqmp is None else iqmp

        return cls(
            key=_RSA.RSAPrivateNumbers(
                public_numbers=_RSA.RSAPublicNumbers(e, n),
                p=p,
                q=q,
                d=d,
                dmp1=_RSA.rsa_crt_dmp1(d, p),
                dmq1=_RSA.rsa_crt_dmq1(d, q),
                iqmp=_RSA.rsa_crt_iqmp(p, q)
            ).private_key()
        )

    @classmethod
    def generate(
        cls,
        key_size: int = 4096,
        public_exponent: int = 65537
    ):
        return cls.from_class(
            _RSA.generate_private_key(
                public_exponent=public_exponent,
                key_size=key_size
            )
        )

    def sign(self, data: bytes, hash_alg: str = 'sha256'):
        if hash_alg not in RSA_SIGNATURE_HASHES.keys():
            raise InvalidHashException("Invalid hash algorithn, needs to be one of {', '.join(RSA_SIGNATURE_HASHES.keys())}")

        return self.key.sign(
            data,
            _PADDING.PKCS1v15(),
            RSA_SIGNATURE_HASHES[hash_alg]()
        )

class DSAPublicKey(PublicKey):
    def __init__(
        self,
        key: _DSA.DSAPublicKey,
        comment: STR_OR_BYTES = None,
        key_type: STR_OR_BYTES = None
    ):
        super().__init__(
            key=key,
            comment=comment,
            key_type=key_type,
            public_numbers=key.public_numbers(),
        )
        self.parameters = key.parameters().parameter_numbers()

    @classmethod
    def from_numbers(
        cls,
        p: int,
        q: int,
        g: int,
        y: int
    ):
        return cls(
            key=_DSA.DSAPublicNumbers(
                y=y,
                parameter_numbers=_DSA.DSAParameterNumbers(
                    p=p,
                    q=q,
                    g=g
                )
            ).public_key()
        )

class DSAPrivateKey(PrivateKey):
    def __init__(self, key: _DSA.DSAPrivateKey):
        super().__init__(
            key=key,
            public_key=DSAPublicKey(
                key.public_key()
            ),
            private_numbers=key.private_numbers()
        )

    @classmethod
    def from_numbers(
        cls,
        p: int,
        q: int,
        g: int,
        y: int,
        x: int
    ):
        return cls(
            key=_DSA.DSAPrivateNumbers(
                public_numbers=_DSA.DSAPublicNumbers(
                    y=y,
                    parameter_numbers=_DSA.DSAParameterNumbers(
                        p=p,
                        q=q,
                        g=g
                    )
                ),
                x=x
            ).private_key()
        )

    @classmethod
    def generate(cls, key_size: int = 4096):
        return cls.from_class(
            _DSA.generate_private_key(
                key_size=key_size
            )
        )

    def sign(self, data: bytes):
       return self.key.sign(
            data,
            _HASHES.SHA1()
        )

class ECDSAPublicKey(PublicKey):
    def __init__(
        self,
        key: _ECDSA.EllipticCurvePublicKey,
        comment: STR_OR_BYTES = None,
        key_type: STR_OR_BYTES = None
    ):
        super().__init__(
            key=key,
            comment=comment,
            key_type=key_type,
            public_numbers=key.public_numbers(),
        )

    @classmethod
    def from_numbers(
        cls,
        curve: CURVE_OR_STRING,
        x: int,
        y: int
    ):
        if not isinstance(curve, _ECDSA.EllipticCurve) and curve not in ECDSA_CURVES.keys():
            raise InvalidCurveException(f"Invalid curve, must be one of {', '.join(ECDSA_CURVES.keys())}")


        return cls(
            key=_ECDSA.EllipticCurvePublicNumbers(
                curve=ECDSA_CURVES[curve]() if isinstance(curve, str) else curve,
                x=x,
                y=y
            ).public_key()
        )

class ECDSAPrivateKey(PrivateKey):
    def __init__(self, key: _ECDSA.EllipticCurvePrivateKey):
        super().__init__(
            key=key,
            public_key=ECDSAPublicKey(
                key.public_key()
            ),
            private_numbers=key.private_numbers()
        )

    @classmethod
    def from_numbers(cls, curve: CURVE_OR_STRING, x: int, y: int, private_value: int):
        if not isinstance(curve, _ECDSA.EllipticCurve) and curve not in ECDSA_CURVES.keys():
            raise InvalidCurveException(f"Invalid curve, must be one of {', '.join(ECDSA_CURVES.keys())}")

        return cls(
            key=_ECDSA.EllipticCurvePrivateNumbers(
                public_numbers=_ECDSA.EllipticCurvePublicNumbers(
                    curve=ECDSA_CURVES[curve]() if isinstance(curve, str) else curve,
                    x=x,
                    y=y
                ),
                private_value=private_value
            ).private_key()
        )

    @classmethod
    def generate(cls, curve: _ECDSA.EllipticCurve):
        return cls.from_class(
            _ECDSA.generate_private_key(
                curve=curve
            )
        )

    def sign(self, data: bytes):
        curve = ECDSA_CURVES[self.key.curve.name]

        return self.key.sign(
            data,
            _ECDSA.ECDSA(curve())
        )

class ED25519PublicKey(PublicKey):
    def __init__(
        self,
        key: _ED25519.Ed25519PublicKey,
        comment: STR_OR_BYTES = None,
        key_type: STR_OR_BYTES = None
    ):
        super().__init__(
            key=key,
            comment=comment,
            key_type=key_type
        )
        
    @classmethod
    def from_raw_bytes(cls, raw_bytes: bytes) -> 'ED25519PublicKey':
        return cls.from_class(
            _ED25519.Ed25519PublicKey.from_public_bytes(
                data=raw_bytes
            )
        )
        
    def raw_bytes(self):
        return self.key.public_bytes(
            encoding=_SERIALIZATION.Encoding.Raw,
            format=_SERIALIZATION.PublicFormat.Raw
        )

class ED25519PrivateKey(PrivateKey):
    def __init__(self, key: _ED25519.Ed25519PrivateKey):
        super().__init__(
            key=key,
            public_key=ED25519PublicKey(
                key.public_key()
            )
        )
    
    @classmethod
    def from_raw_bytes(cls, raw_bytes: bytes) -> 'ED25519PrivateKey':
        return cls.from_class(
            _ED25519.Ed25519PrivateKey.from_private_bytes(
                data=raw_bytes
            )
        )
    
    @classmethod
    def generate(cls):
        return cls.from_class(
            _ED25519.Ed25519PrivateKey.generate()
        )
        
    def raw_bytes(self):
        return self.key.private_bytes(
            encoding=_SERIALIZATION.Encoding.Raw,
            format=_SERIALIZATION.PrivateFormat.Raw,
            encryption_algorithm=_SERIALIZATION.NoEncryption()
        )
        
    def sign(self, data: bytes):
        return self.key.sign(data)