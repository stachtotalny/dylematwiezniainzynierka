export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log("Vercel widzi URL:", process.env.CLOUD_RUN_URL);
    console.log("Długość klucza w Vercelu to:", process.env.CLOUD_RUN_SECRET ? process.env.CLOUD_RUN_SECRET.length : 0);
    
    if (!process.env.CLOUD_RUN_URL) {
      console.error("[PROXY] Błąd: Brak zmiennej CLOUD_RUN_URL");
      return new Response("Błąd konfiguracji serwera", { status: 500 });
    }

    console.log("[PROXY] Wysyłam zapytanie do:", `${process.env.CLOUD_RUN_URL}/api/symulacja`);

    const response = await fetch(`${process.env.CLOUD_RUN_URL}/api/symulacja`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.CLOUD_RUN_SECRET || ''
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      console.error(`[PROXY] Cloud Run zwrócił błąd: ${response.status}`);
      return new Response(`Błąd Cloud Run: ${response.status}`, { status: response.status });
    }

    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      }
    });
  } catch (error) {
    console.error("[PROXY] Krytyczny błąd połączenia:", error);
    return new Response("Krytyczny błąd proxy", { status: 500 });
  }
}
