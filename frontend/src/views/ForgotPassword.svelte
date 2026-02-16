<script>
  export let onBackToLogin = () => {};
</script>

<div class="card">
  <h2>Forgot password?</h2>
  <p class="intro">Use the email and password you used when you registered. If you don’t remember your password, contact your platform administrator or support to reset it.</p>
  <div class="info-box">
    <p><strong>Tip:</strong> Make sure you’re using the same email you used to create your account. Passwords are case-sensitive.</p>
  </div>
  <button type="button" class="btn btn-primary" on:click={onBackToLogin}>Back to Log in</button>
</div>

<style>
  .intro {
    margin-bottom: 1.25rem;
    line-height: 1.5;
    color: var(--text-muted, #555);
  }
  .info-box {
    padding: 1rem;
    background: #f0f7ff;
    border-radius: 8px;
    margin-bottom: 1.25rem;
    font-size: 0.95rem;
  }
  .info-box p { margin: 0; }
</style>
