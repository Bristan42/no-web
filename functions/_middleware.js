// Middleware Pages Functions : bloque l'accès public aux dossiers internes
// (données prospects/clients, CI). Les en-têtes de sécurité sont posés au niveau
// de la zone Cloudflare (Transform Rule "Security headers"), pas ici, pour éviter
// tout double-réglage.
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
    // ne jamais casser le site
  }
  return context.next();
}
