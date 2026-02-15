<script>
  import { claimTokenInfo, claimWithPassword } from '../lib/api.js';

  export let token = '';
  export let onSuccess = () => {};
  export let onCancel = () => {};

  let email = '';
  let uin = '';
  let loading = true;
  let error = '';
  let password = '';
  let confirmPassword = '';
  let submitting = false;
  let claimed = false;

  $: if (token) {
    loadToken();
  }

  async function loadToken() {
    loading = true;
    error = '';
    try {
      const info = await claimTokenInfo(token);
      email = info.email || '';
      uin = info.uin || '';
    } catch (e) {
      error = e.message || 'Invalid or expired link';
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    error = '';
    if (!password || password.length < 10) {
      error = 'Password must be at least 10 characters';
      return;
    }
    if (password !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }
    submitting = true;
    try {
      await claimWithPassword(token, password);
      claimed = true;
    } catch (e) {
      error = e.message || 'Claim failed';
    } finally {
      submitting = false;
    }
  }
</script>

<div class="card">
  <h2>Claim Your Graduate Account</h2>
  {#if loading}
    <p>Checking your link…</p>
  {:else if claimed}
    <div class="alert alert-success">Welcome back! Your graduate account is ready. You can now log in.</div>
    <button class="btn btn-primary" on:click={onSuccess}>Log in</button>
  {:else if error && !email}
    <div class="alert alert-error">{error}</div>
    <p class="hint">This link may have expired or already been used. Request a new one or contact support.</p>
    <button class="btn btn-secondary" on:click={onCancel}>Back to login</button>
  {:else}
    <p class="hint">Set a password for <strong>{email}</strong> to complete your graduation handover. Your student UIN ({uin}) will be linked to this account.</p>
    {#if error}
      <div class="alert alert-error">{error}</div>
    {/if}
    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="claim-password">Password</label>
        <input id="claim-password" type="password" bind:value={password} placeholder="Min 10 characters" minlength="10" />
      </div>
      <div class="form-group">
        <label for="claim-confirm">Confirm password</label>
        <input id="claim-confirm" type="password" bind:value={confirmPassword} placeholder="Same as above" />
      </div>
      <button class="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? 'Claiming…' : 'Claim account'}
      </button>
      <button class="btn btn-secondary" type="button" on:click={onCancel} style="margin-left: 0.5rem;">
        Cancel
      </button>
    </form>
  {/if}
</div>
