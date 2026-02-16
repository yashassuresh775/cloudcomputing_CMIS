<script>
  import { signin, requestMagicLink } from '../lib/api.js';

  export let onLogin = () => {};
  export let onGoToClaim = () => {};
  export let onGoToForgotPassword = () => {};

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  // Graduate claim flow
  let showGraduateFlow = false;
  let graduateEmail = '';
  let requestLoading = false;
  let requestSuccess = null; // { message, magicLink? }
  let showPasteToken = false;
  let claimTokenInput = '';

  async function handleRequestLink() {
    error = '';
    requestSuccess = null;
    const em = graduateEmail.trim().toLowerCase();
    if (!em || !em.includes('@')) {
      error = 'Enter your personal email (the one on your graduation record)';
      return;
    }
    requestLoading = true;
    try {
      const result = await requestMagicLink(em);
      requestSuccess = result;
    } catch (e) {
      error = e.message || 'Request failed';
    } finally {
      requestLoading = false;
    }
  }

  function openClaimFromLink() {
    if (requestSuccess?.magicLink) {
      const match = requestSuccess.magicLink.match(/token=([A-Za-z0-9_-]+)/);
      if (match) onGoToClaim(match[1]);
    }
  }

  function goToClaimFromPaste() {
    let token = claimTokenInput.trim();
    const match = token.match(/token=([A-Za-z0-9_-]+)/);
    if (match) token = match[1];
    token = token.trim();
    if (token) {
      onGoToClaim(token);
    } else {
      error = 'Please paste your claim token or magic link URL';
    }
  }

  function resetGraduateFlow() {
    showGraduateFlow = false;
    graduateEmail = '';
    requestSuccess = null;
    error = '';
  }

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
  <p class="hint sso-note">Sign in with your @tamu.edu email. Use your CMIS account password (SSO is not used).</p>
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
    {#if onGoToForgotPassword}
      <button type="button" class="btn btn-link" style="margin-left: 0.5rem;" on:click={onGoToForgotPassword}>Forgot password?</button>
    {/if}
  </form>

  <div class="claim-section">
    <h3 class="claim-heading">Recent graduate?</h3>
    <p class="hint">Claim your CMIS account using the personal email on your student record.</p>

    {#if showGraduateFlow}
      {#if requestSuccess}
        <div class="alert alert-success">{requestSuccess.message}</div>
        {#if requestSuccess.magicLink}
          <button type="button" class="btn btn-primary claim-cta" on:click={openClaimFromLink}>
            Open claim page →
          </button>
        {/if}
        <button type="button" class="btn btn-link" on:click={resetGraduateFlow}>Start over</button>
      {:else}
        <div class="claim-input-row">
          <input
            type="email"
            bind:value={graduateEmail}
            placeholder="Your personal email (e.g. you@gmail.com)"
            class="claim-token-input"
            disabled={requestLoading}
          />
          <button type="button" class="btn btn-primary" on:click={handleRequestLink} disabled={requestLoading}>
            {requestLoading ? 'Sending…' : 'Get my claim link'}
          </button>
        </div>
        <button type="button" class="btn btn-link" on:click={resetGraduateFlow}>Cancel</button>
      {/if}
    {:else}
      <button type="button" class="btn btn-secondary" on:click={() => { showGraduateFlow = true; error = ''; requestSuccess = null; }}>
        I'm a graduate — get my claim link
      </button>
    {/if}

    <div class="claim-paste">
      <button type="button" class="btn btn-link" on:click={() => { showPasteToken = !showPasteToken; error = ''; }}>
        {showPasteToken ? '▼' : '▶'} Already have a magic link? Paste it here
      </button>
      {#if showPasteToken}
        <div class="claim-input-row">
          <input
            type="text"
            bind:value={claimTokenInput}
            placeholder="Paste token or full URL"
            class="claim-token-input"
          />
          <button type="button" class="btn btn-primary" on:click={goToClaimFromPaste}>
            Go to claim
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .claim-section {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color, #ddd);
  }
  .claim-heading {
    font-size: 1rem;
    margin: 0 0 0.25rem 0;
    color: var(--text-color, #333);
  }
  .claim-input-row {
    display: flex;
    gap: 0.5rem;
    margin: 0.5rem 0;
    flex-wrap: wrap;
  }
  .claim-token-input {
    flex: 1;
    min-width: 200px;
    padding: 0.5rem;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
  }
  .claim-cta {
    margin: 0.5rem 0;
  }
  .claim-paste {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px dashed var(--border-color, #ddd);
  }
  .btn-link {
    background: none;
    border: none;
    color: var(--primary-color, #0066cc);
    cursor: pointer;
    padding: 0.25rem 0;
    font-size: 0.95rem;
  }
  .btn-link:hover {
    text-decoration: underline;
  }
</style>
