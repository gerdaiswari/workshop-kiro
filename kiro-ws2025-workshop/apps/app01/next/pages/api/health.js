export default function handler(_request, response) {
  response.status(200).json({
    status: 'ok',
    application: 'kiro-workshop-next',
    marker: 'NEXT_API_OK_V1',
    host: process.env.COMPUTERNAME || 'unknown'
  });
}
