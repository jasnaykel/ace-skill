"""Parametriza la collection Postman de la plantilla con el contrato real.

Reescribir 6 cuerpos a mano (3 ambientes x 2 canales) es la via rapida de
meter un dato equivocado y no notarlo. Aqui se hace una sola pasada sobre el
JSON y se comprueba que no queda ni un residuo del servicio de origen.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

COLECCION = Path(sys.argv[1])
NOMBRE_FUNCIONAL = "Listado Cobranza Libre PJ"
HOST = "retrieve-collections-free-pj"
OPERACION = "RetrieveCPSDProductCollectionListCorporate"
COD_SERVICIO = "CSH012"

BODY = {
    OPERACION: {
        "ServiceType": COD_SERVICIO,
        "CustomerReference": "000123456",
        "NumberOfPage": "001",
    }
}

HEADERS = {
    "Content-Type": "application/json",
    "Bif-Consumer-Id": "APP205",
    "Bif-Mdw-Id": "APP212",
    "Bif-Correlation-Id": "31a738b2-2e0f-49b9-9f1f-a6cfea8c506a",
    "Time-Stamp": "2025-04-01T21:30:05.660Z",
}

RESIDUOS = (
    "update-reverse-payment-collections-ibs",
    "Reversar Pago IBS",
    "CSH001",
    "153",
)


def recorrer(items):
    for item in items:
        yield item
        yield from recorrer(item.get("item", []))


def main() -> int:
    datos = json.loads(COLECCION.read_text(encoding="utf-8"))

    datos["info"]["name"] = f"ACE 147 {NOMBRE_FUNCIONAL} IBS"
    datos["info"]["description"] = (
        "Usar credenciales de usuarios AD para cada ambiente. "
        "El certificado cliente mTLS debe estar configurado en Postman."
    )

    peticiones = 0
    for item in recorrer(datos.get("item", [])):
        peticion = item.get("request")
        if not peticion:
            continue
        peticiones += 1

        if item.get("name") == "Reversar Pago IBS":
            item["name"] = NOMBRE_FUNCIONAL

        url = peticion.get("url")
        if isinstance(url, dict):
            url["raw"] = url["raw"].replace(
                "update-reverse-payment-collections-ibs", HOST
            )
            for parte in url.get("host", []):
                if parte == "update-reverse-payment-collections-ibs":
                    url["host"][url["host"].index(parte)] = HOST
        elif isinstance(url, str):
            peticion["url"] = url.replace("update-reverse-payment-collections-ibs", HOST)

        if peticion.get("method") == "POST":
            peticion["body"] = {
                "mode": "raw",
                "raw": json.dumps(BODY, indent=2, ensure_ascii=False),
                "options": {"raw": {"language": "json"}},
            }
            claves = {h["key"]: h for h in peticion.get("header", [])}
            for clave, valor in HEADERS.items():
                if clave in claves:
                    claves[clave]["value"] = valor
                    claves[clave]["disabled"] = False
                else:
                    peticion.setdefault("header", []).append(
                        {"key": clave, "value": valor, "type": "text"}
                    )
            # Authorization es obligatoria en la fachada y no viaja como Basic
            # Auth de Postman: se deja marcada para completar con el valor real.
            if "Authorization" not in claves:
                peticion["header"].append(
                    {
                        "key": "Authorization",
                        "value": "COMPLETAR_CREDENCIAL_ONPREMISE",
                        "type": "text",
                    }
                )

    COLECCION.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    texto = COLECCION.read_text(encoding="utf-8")
    print(f"peticiones parametrizadas: {peticiones}")
    for residuo in RESIDUOS:
        if residuo in texto:
            print(f"BLOQUEANTE: queda el residuo '{residuo}'")
            return 2
    print("OK: sin residuos del servicio de origen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
