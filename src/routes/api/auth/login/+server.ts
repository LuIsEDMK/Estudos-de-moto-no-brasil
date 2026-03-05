import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getUserFromCredential } from '$lib/server/auth';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const formData = await request.formData();
	const credential = formData.get('credential') as string;

	if (!credential) {
		return json({ vip: false, google_ok: false });
	}

	try {
		const user = await getUserFromCredential(credential);

		if (!user) {
			return json({ vip: false, google_ok: false });
		}

		if (user.vip) {
			cookies.set('vip_token', '1', {
				path: '/',
				httpOnly: true,
				maxAge: 60 * 60 * 24 * 7 // 7 days
			});
			cookies.set('user_email', user.email, {
				path: '/',
				maxAge: 60 * 60 * 24 * 7
			});
		}

		return json({
			vip: user.vip,
			google_ok: true,
			email: user.email
		});
	} catch (e) {
		console.error('Login error:', e);
		return json({ vip: false, google_ok: false });
	}
};
