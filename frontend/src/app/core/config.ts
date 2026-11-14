// Адрес Django API: тот же компьютер, что отдал сайт, порт 8000.
// Благодаря этому сайт работает и по localhost, и с телефона по адресу компьютера в сети Wi-Fi.
export const API_URL = `http://${window.location.hostname}:8000/api`;

/** Достаёт код check-in из ссылки вида .../checkin/<код> или из самого кода. */
export function extractCheckinToken(text: string): string | null {
  const match = text.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
  return match ? match[0].toLowerCase() : null;
}
