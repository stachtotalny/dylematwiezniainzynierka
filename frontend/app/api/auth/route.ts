import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const { password } = await req.json();
  if (password === process.env.SITE_PASSWORD) {
    const response = NextResponse.json({ success: true });
    response.cookies.set('site_auth', 'authenticated', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    });
    return response;
  }
  return NextResponse.json({ success: false }, { status: 401 });
}
