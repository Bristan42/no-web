// Bloque l'accès public aux dossiers internes (outils, données prospects/clients, CI).
// Un middleware Pages Functions s'exécute AVANT le service des fichiers statiques
// (contrairement à _redirects, qui ne peut pas masquer un fichier existant).
const BLOCKED = ["/_template-macon", "/_template-plombier", "/.github"];

export async function onRequest(context) {
  try {
    const path = new URL(context.request.url).pathname;
    if (BLOCKED.some((p) => path === p || path.startsWith(p + "/"))) {
      return new Response("Not Found", {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
  } catch (e) {
    // Ne jamais casser le site en cas d'erreur : on laisse passer.
  }
  return context.next();
}
