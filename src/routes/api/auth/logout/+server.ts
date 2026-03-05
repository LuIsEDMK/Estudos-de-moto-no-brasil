import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ cookies }) => {
	cookies.delete('vip_token', { path: '/' });
	cookies.delete('user_email', { path: '/' });
	cookies.delete('consultas', { path: '/' });

	return json({ success: true });
};
