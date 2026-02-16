<script>
  import { forgotPassword, resetPassword } from '../lib/api.js';

  export let onDone = () => {};
  export let onBack = () => {};

  let email = '';
  let step = 'email'; // 'email' | 'code'
  let code = '';
  let newPassword = '';
  let confirmPassword = '';
  let loading = false;
  let error = '';
  let success = '';

  async function requestCode() {
    error = '';
    const em = email.trim().toLowerCase();
    if (!em || !em.includes('@')) {
      error = 'Enter your email address';
      return;
    }
    loading = true;
    try {
      await forgotPassword(em);
      step = 'code';
      success = 'Check your email for the reset code.';
    } catch (e) {
      error = e.message || 'Request failed';
    } finally {
      loading = false;
    }
  }

  async function submitReset() {
    error = '';
    if (!code.trim()) {
      error = 'Enter the code from your email';
      return;
    }
    if (!newPassword || newPassword.length < 10) {
      error = 'New password must be at least 10 characters';
      return;
    }
    if (newPassword !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }
    loading = true;
    try {
      await resetPassword({
        email: email.trim().toLowerCase(),
        code: code.trim(),
        newPassword,
      });
      success = 'Password has been reset. You can sign in with your new password.';
      setTimeout(() => onDone(), 2000);
    } catch (e) {
      error = e.message || 'Reset failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <h2>Forgot password</h2>
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  {#if success}
    <div class="alert alert-success">{success}</div>
  {/if}

  {#if step === 'email'}
    <p class="hint">Enter your email and we'll send you a code to reset your password.</p>
    <form on:submit|preventDefault={requestCode}>
      <div class="form-group">
        <label for="fp-email">Email</label>
        <input id="fp-email" type="email" bind:value={email} placeholder="you@tamu.edu" disabled={loading} />
      </div>
      <button class="btn btn-primary" type="submit" disabled={loading}>
        {loading ? 'Sending…' : 'Send reset code'}
      </button>
    </form>
  {:else}
    <p class="hint">Enter the code from your email and choose a new password.</p>
    <form on:submit|preventDefault={submitReset}>
      <div class="form-group">
        <label for="fp-code">Reset code</label>
        <input id="fp-code" type="text" bind:value={code} placeholder="123456" disabled={loading} />
      </div>
      <div class="form-group">
        <label for="fp-new">New password</label>
        <input id="fp-new" type="password" bind:value={newPassword} placeholder="At least 10 characters" disabled={loading} />
      </div>
      <div class="form-group">
        <label for="fp-confirm">Confirm new password</label>
        <input id="fp-confirm" type="password" bind:value={confirmPassword} placeholder="Repeat password" disabled={loading} />
      </div>
      <button class="btn btn-primary" type="submit" disabled={loading}>
        {loading ? 'Resetting…' : 'Reset password'}
      </button>
    </form>
  {/if}

  <button class="btn btn-link" style="margin-top: 1rem;" on:click={onBack}>Back to log in</button>
</div>
