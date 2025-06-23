from nvdlib import searchCVE
from datetime import datetime
import textwrap

def format_cve(cve_objects):
    """Formatea objetos CVE para una salida legible."""
    for cve in cve_objects:
        print("\n" + "=" * 80)
        print(f"\033[1;31mCVE ID:\033[0m \033[1m{cve.id}\033[0m")
        print(f"\033[1;34mEstado:\033[0m {getattr(cve, 'vulnStatus', 'Desconocido')}")
        print(f"\033[1;34mPublicado:\033[0m {cve.published}")
        print(f"\033[1;34mÚltima modificación:\033[0m {cve.lastModified}")

        # Descripciones (priorizando español)
        en_desc = next((desc.value for desc in cve.descriptions if desc.lang == 'en'), "Sin descripción")
        es_desc = next((desc.value for desc in cve.descriptions if desc.lang == 'es'), None)

        print("\n\033[1;33mDESCRIPCIÓN:\033[0m")
        print(textwrap.fill(es_desc if es_desc else en_desc, width=80))

        # CVSS v3.1
        if hasattr(cve, 'metrics') and getattr(cve.metrics, 'cvssMetricV31', None):
            cvss = cve.metrics.cvssMetricV31[0].cvssData
            print("\n\033[1;33mCVSS v3.1:\033[0m")
            print(f"  \033[1;36mPuntuación:\033[0m {cvss.baseScore} ({cvss.baseSeverity})")
            print(f"  \033[1;36mVector:\033[0m {cvss.vectorString}")
            print(
                f"  \033[1;36mImpacto:\033[0m Confidencialidad: {cvss.confidentialityImpact}, Integridad: {cvss.integrityImpact}, Disponibilidad: {cvss.availabilityImpact}")

        # Productos afectados (CPE)
        if hasattr(cve, 'configurations'):
            print("\n\033[1;33mSISTEMAS AFECTADOS:\033[0m")
            for node in cve.configurations[0].nodes:
                for match in node.cpeMatch:
                    if match.vulnerable:
                        version_info = f" (Versiones anteriores a {match.versionEndExcluding})" if hasattr(match,'versionEndExcluding') else ""
                        print(f"  - {match.criteria}{version_info}")

        # Referencias
        if hasattr(cve, 'references'):
            print("\n\033[1;33mREFERENCIAS:\033[0m")
            for ref in cve.references[:3]:  # Mostrar solo 3
                tags = ', '.join(ref.tags) if hasattr(ref, 'tags') else ''
                print(f"  - {ref.url} ({tags})")

        print("=" * 80 + "\n")

def analizar_archivo_sbom(path):
    results = searchCVE(cveId="CVE-2024-1234")  # o escaneas el SBOM en busca de ids reales
    if not results:
        return "No se encontraron vulnerabilidades en el archivo."

    cve = results[0]
    resumen = f"CVE ID: {cve.id}\nPublicado: {cve.published}\nDescripción: {cve.descriptions[0].value}"
    return textwrap.shorten(resumen, width=400)