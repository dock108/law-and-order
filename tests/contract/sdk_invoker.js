const createClient = require('@pi-monorepo/api-client').default;

async function main() {
  const operationId = process.argv[2];

  let inputJson = '';
  process.stdin.on('readable', () => {
    let chunk;
    while (null !== (chunk = process.stdin.read())) {
      inputJson += chunk;
    }
  });

  process.stdin.on('end', async () => {
    const inputData = JSON.parse(inputJson || '{}');
    const params = inputData.params;
    const data = inputData.data;

    const baseUrl = process.env.API_BASE_URL_FOR_SDK_TESTS || 'http://localhost:8000';
    const client = createClient({ baseUrl });

    try {
      let response;
      switch (operationId) {
        case 'AuthLogin': // Matches operationId in OpenAPI for POST /auth/login
          if (!client.POST) {
            console.error('SDK does not have POST method');
            process.exit(1);
          }
          response = await client.POST('/auth/login', { body: data });
          break;
        // Add cases for other operationIds as needed
        default:
          console.error(`Unknown operationId: ${operationId}`);
          process.exit(1);
      }

      if (response.error) {
        console.log(
          JSON.stringify({
            status: response.response.status,
            error: response.error,
            data: response.data,
          })
        );
      } else {
        console.log(
          JSON.stringify({
            status: response.response.status,
            data: response.data,
          })
        );
      }
    } catch (error) {
      console.error('SDK invoker script error:', error);
      const status = error.response ? error.response.status : 500;
      console.log(JSON.stringify({ status: status, error: error.message, data: null }));
      process.exit(1);
    }
  });
}

main();
