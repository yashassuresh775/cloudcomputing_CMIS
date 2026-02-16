<script>
  import { onMount } from 'svelte';
  import Register from './views/Register.svelte';
  import Login from './views/Login.svelte';
  import Handover from './views/Handover.svelte';
  import HandoverHistory from './views/HandoverHistory.svelte';
  import Profile from './views/Profile.svelte';
  import Claim from './views/Claim.svelte';
  import ForgotPassword from './views/ForgotPassword.svelte';
  import ResetPassword from './views/ResetPassword.svelte';

  let view = 'login';
  let claimToken = '';

  onMount(() => {
    const hash = (typeof window !== 'undefined' && window.location.hash) || '';
    const search = (typeof window !== 'undefined' && window.location.search) || '';
    const params = new URLSearchParams(hash.slice(1).split('?')[1] || search.slice(1));
    const token = params.get('token');
    if (token && (hash.includes('claim') || search.includes('token='))) {
      claimToken = token;
      view = 'claim';
    }
    if (params.get('reset') === '1' || (typeof window !== 'undefined' && window.location.pathname === '/reset-password')) {
      view = 'resetPassword';
    }
  });
  let accessToken = localStorage.getItem('accessToken') || '';
  let user = null;

  function setView(v) {
    view = v;
  }

  function onLogin(payload) {
    accessToken = payload.accessToken;
    user = payload.user;
    localStorage.setItem('accessToken', payload.accessToken);
    if (payload.refreshToken) localStorage.setItem('refreshToken', payload.refreshToken);
    view = 'profile';
  }

  function onRegister() {
    view = 'login';
  }

  function onLogout() {
    accessToken = '';
    user = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    view = 'login';
  }

  function onHandoverDone(updatedUser) {
    user = updatedUser;
    view = 'profile';
  }

  function onProfileUpdate(updatedUser) {
    user = updatedUser;
  }

  function onClaimSuccess() {
    claimToken = '';
    view = 'login';
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname || '/');
    }
  }

  function onClaimCancel() {
    claimToken = '';
    view = 'login';
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname || '/');
    }
  }
</script>

<main>
  <div class="container">
    <h1>CMIS Engagement Platform</h1>
    <p class="subtitle">External Core — Partner / Former Student / Friend</p>

    <nav class="nav-links">
      {#if accessToken}
        <button class="btn btn-secondary" on:click={() => setView('profile')}>Profile</button>
        {#if user && user.role !== 'FORMER_STUDENT'}
          <button class="btn btn-secondary" on:click={() => setView('handover')}>Graduation Handover</button>
        {/if}
        <button class="btn btn-secondary" on:click={() => setView('handoverHistory')}>Handover History</button>
        <button class="btn btn-secondary" on:click={onLogout}>Log out</button>
      {:else}
        <button class="btn btn-secondary" on:click={() => setView('login')}>Log in</button>
        <button class="btn btn-secondary" on:click={() => setView('register')}>Register</button>
      {/if}
    </nav>

    {#if view === 'claim'}
      <Claim token={claimToken} onSuccess={onClaimSuccess} onCancel={onClaimCancel} />
    {:else if view === 'register'}
      <Register onDone={onRegister} />
    {:else if view === 'login'}
      <Login onLogin={onLogin} onGoToClaim={(token) => { claimToken = token; view = 'claim'; }} onGoToForgotPassword={() => setView('forgotPassword')} />
    {:else if view === 'forgotPassword'}
      <ForgotPassword onDone={() => setView('login')} onBack={() => setView('login')} />
    {:else if view === 'resetPassword'}
      <ResetPassword onDone={() => setView('login')} onBack={() => setView('login')} />
    {:else if view === 'profile'}
      <Profile {accessToken} {user} onLogout={onLogout} onProfileUpdate={onProfileUpdate} />
    {:else if view === 'handover'}
      <Handover {accessToken} onDone={onHandoverDone} onCancel={() => setView('profile')} />
    {:else if view === 'handoverHistory'}
      <HandoverHistory {accessToken} onBack={() => setView('profile')} />
    {/if}
  </div>
</main>

<style>
  .subtitle {
    color: var(--text-muted);
    margin-top: -0.5rem;
    margin-bottom: 1rem;
  }
</style>
