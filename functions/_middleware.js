// Middleware Pages Functions (s'exécute pour chaque requête) :
//  1) bloque l'accès public aux dossiers internes (données prospects/clients, CI) ;
//  2) applique les en-têtes de sécurité de façon FIABLE (une réponse servie via une
//     Function ne reçoit pas toujours les règles du fichier _headers).
const BLOCKED = ["/_template-macon", "/_template-plombier", "/.github"];

const SECURITY_HEADERS = {
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), browsing-topics=()",
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://api.web3forms.com; form-action 'self' https://api.web3forms.com; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests",
};

export async function onRequest(context) {
  try {
    const path = new URL(context.request.url).pathname;
    if (BLOCKED.some((p) => path === p || path.startsWith(p + "/"))) {
      return new Response("Not Found", {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
    const response = await context.next();
    const headers = new Headers(response.headers);
    for (const [k, v] of Object.entries(SECURITY_HEADERS)) headers.set(k, v);
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (e) {
    // Ne jamais casser le site : on sert la réponse normale.
    return context.next();
  }
}
