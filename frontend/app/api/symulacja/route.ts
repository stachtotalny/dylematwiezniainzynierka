export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    const response = await fetch(`${process.env.CLOUD_RUN_URL}/api/symulacja`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.CLOUD_RUN_SECRET || ''
      },
      body: JSON.stringify(body)
    });
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      }
    });
  } catch (error) {
    return new Response("Błąd serwera", { status: 500 });
  }
}
