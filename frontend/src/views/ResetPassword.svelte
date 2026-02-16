<script>
  import { resetPassword } from '../lib/api.js';
  import { onMount } from 'svelte';

  export let onDone = () => {};
  export let onBack = () => {};

  let email = '';
  let code = '';
  let newPassword = '';
  let confirmPassword = '';
  let loading = false;
  let error = '';
  let success = '';

  onMount(() => {
    const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
    email = params.get('email') || '';
    code = params.get('code') || '';
  });

  async function submitReset() {
    error = '';
    const em = email.trim().toLowerCase();
    if (!em || !em.includes('@')) {
      error = 'Enter your email address';
      return;
    }
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
        email: em,
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
  <h2>Reset password</h2>
  <p class="hint">Set a new password using the code we sent to your email.</p>
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  {#if success}
    <div class="alert alert-success">{success}</div>
  {:else}
    <form on:submit|preventDefault={submitReset}>
      <div class="form-group">
        <label for="rp-email">Email</label>
        <input id="rp-email" type="email" bind:value={email} placeholder="you@tamu.edu" disabled={loading} />
      </div>
      <div class="form-group">
        <label for="rp-code">Reset code</label>
        <input id="rp-code" type="text" bind:value={code} placeholder="123456" disabled={loading} />
      </div>
      <div class="form-group">
        <label for="rp-new">New password</label>
        <input id="rp-new" type="password" bind:value={newPassword} placeholder="At least 10 characters" disabled={loading} />
      </div>
      <div class="form-group">
        <label for="rp-confirm">Confirm new password</label>
        <input id="rp-confirm" type="password" bind:value={confirmPassword} placeholder="Repeat password" disabled={loading} />
      </div>
      <button class="btn btn-primary" type="submit" disabled={loading}>
        {loading ? 'Resetting…' : 'Reset password'}
      </button>
    </form>
  {/if}

  <button class="btn btn-link" style="margin-top: 1rem;" on:click={onBack}>Back to log in</button>
</div>
