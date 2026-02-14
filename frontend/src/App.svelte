<script>
  import Register from './views/Register.svelte';
  import Login from './views/Login.svelte';
  import Handover from './views/Handover.svelte';
  import Profile from './views/Profile.svelte';

  let view = 'login';
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
</script>

<main>
  <div class="container">
    <h1>CMIS Engagement Platform</h1>
    <p class="subtitle">External Core — Partner / Former Student / Friend</p>

    <nav class="nav-links">
      {#if accessToken}
        <button class="btn btn-secondary" on:click={() => setView('profile')}>Profile</button>
        <button class="btn btn-secondary" on:click={() => setView('handover')}>Graduation Handover</button>
        <button class="btn btn-secondary" on:click={onLogout}>Log out</button>
      {:else}
        <button class="btn btn-secondary" on:click={() => setView('login')}>Log in</button>
        <button class="btn btn-secondary" on:click={() => setView('register')}>Register</button>
      {/if}
    </nav>

    {#if view === 'register'}
      <Register onDone={onRegister} />
    {:else if view === 'login'}
      <Login onLogin={onLogin} />
    {:else if view === 'profile'}
      <Profile {accessToken} {user} onLogout={onLogout} />
    {:else if view === 'handover'}
      <Handover {accessToken} onDone={onHandoverDone} onCancel={() => setView('profile')} />
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
