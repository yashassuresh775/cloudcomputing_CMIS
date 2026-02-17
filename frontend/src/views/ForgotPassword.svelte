<script>
  import { forgotPassword } from '../lib/api.js';

  export let onBackToLogin = () => {};
  /** Called after code was sent; pass email so user can go to reset-password page */
  export let onSentResetCode = (email) => {};

  let email = '';
  let loading = false;
  let error = '';
  let sent = false;

  async function sendResetCode() {
    error = '';
    const em = email.trim().toLowerCase();
    if (!em || !em.includes('@')) {
      error = 'Enter your email address';
      return;
    }
    loading = true;
    try {
      await forgotPassword(em);
      sent = true;
      onSentResetCode(em);
    } catch (e) {
      error = e.message || 'Could not send reset code';
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <h2>Forgot password?</h2>
  <p class="intro">Enter your email and we’ll send you a code to set a new password. Check your inbox (and spam folder).</p>

  {#if sent}
    <div class="alert alert-success">
      <strong>Check your email.</strong> We sent a reset code to <strong>{email.trim().toLowerCase()}</strong>. Use the code on the next screen to set your new password.
    </div>
    <button type="button" class="btn btn-primary" on:click={() => onSentResetCode(email.trim().toLowerCase())}>
      Set new password
    </button>
  {:else}
    <form on:submit|preventDefault={sendResetCode}>
      {#if error}
        <div class="alert alert-error">{error}</div>
      {/if}
      <div class="form-group">
        <label for="fp-email">Email</label>
        <input
          id="fp-email"
          type="email"
          bind:value={email}
          placeholder="you@example.com"
          disabled={loading}
          autocomplete="email"
        />
      </div>
      <button type="submit" class="btn btn-primary" disabled={loading}>
        {loading ? 'Sending…' : 'Send reset code to my email'}
      </button>
    </form>
  {/if}

  <button type="button" class="btn btn-link" style="margin-top: 1rem;" on:click={onBackToLogin}>
    Back to Log in
  </button>
</div>

<style>
  .intro {
    margin-bottom: 1.25rem;
    line-height: 1.5;
    color: var(--text-muted);
  }
  .info-box {
    padding: 1rem;
    background: linear-gradient(135deg, rgba(80, 0, 0, 0.06), rgba(122, 0, 0, 0.04));
    border-left: 4px solid var(--primary-color);
    border-radius: 8px;
    margin-bottom: 1.25rem;
    font-size: 0.95rem;
    animation: fadeIn 0.4s ease-out 0.15s backwards;
  }
  .info-box p { margin: 0; }
</style>
