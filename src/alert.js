// Manager notification (stub): one JSON line per escalated ticket.
// In production swap the next node for Telegram / Slack / Gmail.
const t = $('Build reply').first().json;
const kb = ((j) => j.data && j.data.faqs ? j.data : j)($('Parse FAQ file').first().json);
const alert = {
  sent_at: new Date().toISOString(),
  to: kb.manager_contact,
  priority: t.priority,
  reason: t.escalation_reason,
  ticket_id: t.ticket_id,
  customer: `${t.name} <${t.email}>`,
  subject: `[${t.priority.toUpperCase()}] ${t.category} from ${t.name}`,
  message: t.message,
};
const line = JSON.stringify(alert) + '\n';
return [{
  json: alert,
  binary: { data: { data: Buffer.from(line, 'utf8').toString('base64'), mimeType: 'application/json', fileName: 'manager_alerts.jsonl', fileExtension: 'jsonl' } },
}];
