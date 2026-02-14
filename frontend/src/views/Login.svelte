<script>
  import { signin } from '../lib/api.js';

  export let onLogin = () => {};

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleSubmit() {
    error = '';
    if (!email.trim() || !password) {
      error = 'Email and password are required';
      return;
    }
    loading = true;
    try {
      const data = await signin({
        email: email.trim().toLowerCase(),
        password,
      });
      onLogin({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        user: data.user,
      });
    } catch (e) {
      error = e.message || 'Sign in failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <h2>Log in</h2>
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="login-email">Email</label>
      <input id="login-email" type="email" bind:value={email} required />
    </div>
    <div class="form-group">
      <label for="login-password">Password</label>
      <input id="login-password" type="password" bind:value={password} required />
    </div>
    <button class="btn btn-primary" type="submit" disabled={loading}>
      {loading ? 'Signing in…' : 'Log in'}
    </button>
  </form>
</div>
