export type LoginResponse = {
  access_token: string
  email: string
  name: string
  role: string
}

const loginEndpoint =
  import.meta.env.VITE_LOGIN_ENDPOINT ?? 'http://127.0.0.1:8001/api/v1/login'

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(loginEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  const result = await response.json()

  if (!response.ok) {
    throw new Error(
      typeof result.detail === 'string' ? result.detail : 'Login failed',
    )
  }

  return result as LoginResponse
}