from __future__ import annotations

import ssl

import requests
from requests.adapters import HTTPAdapter
import truststore


class SystemTrustHTTPAdapter(HTTPAdapter):
    """Requests adapter backed by the OS trust store with hostname checks on."""

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs["ssl_context"] = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )
        return super().init_poolmanager(
            connections,
            maxsize,
            block=block,
            **pool_kwargs,
        )

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs["ssl_context"] = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def crear_session_system_trust() -> requests.Session:
    """Create an HTTP session that validates TLS with the system trust store."""
    session = requests.Session()
    adapter = SystemTrustHTTPAdapter()
    session.mount("https://", adapter)
    return session
