import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { criarAssinante } from '$lib/server/sheets/assinantes';

/**
 * Webhook para receber notificações do Mercado Pago
 * 
 * Configuração no dashboard do Mercado Pago:
 * URL: https://seusite.com/api/webhooks/mercado-pago
 * Events: payment.created, payment.updated
 */

export const POST: RequestHandler = async ({ request }) => {
	try {
		// Verifica assinatura do webhook (segurança)
		const signature = request.headers.get('x-signature');
		const body = await request.text();

		if (!verifyMercadoPagoSignature(body, signature)) {
			throw error(401, 'Assinatura inválida');
		}

		const data = JSON.parse(body);

		// Processa apenas pagamentos aprovados
		if (data.type === 'payment' && data.data?.id) {
			await processPayment(data.data.id);
		}

		return json({ success: true });
	} catch (err) {
		console.error('Webhook error:', err);
		// Sempre retorna 200 para o Mercado Pago não reenviar
		return json({ success: false, error: 'Processing failed' });
	}
};

async function processPayment(paymentId: string) {
	// Busca detalhes do pagamento na API do Mercado Pago
	const payment = await fetchMercadoPagoPayment(paymentId);

	if (payment.status !== 'approved') {
		console.log('Pagamento não aprovado:', payment.status);
		return;
	}

	// Extrai informações do pagamento
	const email = payment.payer?.email || payment.external_reference;
	const amount = payment.transaction_amount;

	// Determina o plano baseado no valor
	const planoInfo = getPlanoByValue(amount);

	if (!email) {
		console.error('Email não encontrado no pagamento');
		return;
	}

	// Cria assinante no Google Sheets
	const success = await criarAssinante({
		email,
		plano: planoInfo.nome,
		dias: planoInfo.dias,
		vendedores: planoInfo.vendedores
	});

	if (success) {
		console.log('Assinante criado:', email, planoInfo.nome);
	}
}

async function fetchMercadoPagoPayment(paymentId: string) {
	const accessToken = process.env.MERCADO_PAGO_ACCESS_TOKEN;

	const response = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
		headers: {
			'Authorization': `Bearer ${accessToken}`
		}
	});

	if (!response.ok) {
		throw new Error(`Failed to fetch payment: ${response.status}`);
	}

	return response.json();
}

function getPlanoByValue(amount: number): { nome: string; dias: number; vendedores?: string[] } {
	// Define planos baseado nos valores
	if (amount >= 150) {
		return { nome: 'Agência VIP', dias: 30, vendedores: [] };
	} else if (amount >= 50) {
		return { nome: 'Garagista PRO', dias: 30 };
	} else {
		return { nome: 'Passaporte', dias: 30 };
	}
}

// Verificação de assinatura do webhook (implementação básica)
function verifyMercadoPagoSignature(body: string, signature: string | null): boolean {
	// Em produção, implementar verificação completa com secret
	// https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks#validar-origem-da-notificacao
	return true; // Simplificado para desenvolvimento
}
