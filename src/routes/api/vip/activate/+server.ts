import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ cookies, request }) => {
    console.log('[API VIP Activate] Request headers:', Object.fromEntries(request.headers));
    
    // Seta o cookie vip_token - simplificado para localhost
    cookies.set('vip_token', '1', {
        path: '/',
        maxAge: 60 * 60 * 24, // 1 dia
        httpOnly: false,
        sameSite: 'lax'
    });
    
    // Seta também o cookie de sessão
    cookies.set('vip_session', Buffer.from(JSON.stringify({ vip: true, user: null })).toString('base64'), {
        path: '/',
        maxAge: 60 * 60 * 24,
        httpOnly: false,
        sameSite: 'lax'
    });
    
    // Log dos cookies que foram setados
    const allCookies = cookies.getAll();
    console.log('[API VIP Activate] Cookies setados no servidor:', allCookies);
    
    // Retorna com header específico para permitir cookies
    return new Response(JSON.stringify({ 
        success: true, 
        message: 'VIP ativado', 
        cookies: allCookies.map(c => c.name) 
    }), {
        status: 200,
        headers: {
            'Content-Type': 'application/json'
        }
    });
};
