# Deploying the demo

Two services: the FastAPI backend on **Render**, the Next.js frontend on
**Vercel**. Both free tiers. Budget about 15 minutes, most of it waiting on
the first Docker build.

Deploy the backend first — the frontend needs its URL.

---

## 1. Backend → Render

1. <https://dashboard.render.com> → **New** → **Blueprint**.
2. Connect the GitHub repo and pick the branch. Render reads `render.yaml`
   from the repository root and proposes one service, `pavo-cloud-api`.
3. It will ask for the values marked `sync: false`:

   | Variable | Value |
   |---|---|
   | `DEEPSEEK_API_KEY` | your DeepSeek key |

   Leave it blank if you would rather demo without the model — the app falls
   back to labelled sample data and every other step is unaffected.
4. **Apply**. The first build takes 5–10 minutes (it installs Python deps,
   then snarkjs).
5. Copy the service URL, e.g. `https://pavo-cloud-api.onrender.com`.
6. Confirm it is alive:

   ```
   curl https://pavo-cloud-api.onrender.com/health
   ```

   Expect `"status":"ok"` and `"zk_artifacts_available":true`. If that last
   field is `false`, the ZK artifacts did not make it into the image and demo
   step 3 will fail — check that `zk/artifacts/` is committed.

---

## 2. Frontend → Vercel

1. <https://vercel.com/new> → import the same repo.
2. **Set Root Directory to `frontend`.** This is the one setting Vercel
   cannot infer and the one that breaks the build if missed.
3. Add one environment variable:

   | Variable | Value |
   |---|---|
   | `BACKEND_ORIGIN` | the Render URL from step 1, no trailing slash |

   That is the whole configuration. Do **not** set
   `NEXT_PUBLIC_API_BASE_URL` — leaving it unset is what routes API calls
   through the proxy.
4. **Deploy**, then open `https://<your-app>.vercel.app/demo` and press
   **Run Full Demo**. All six steps should go green in about 11 seconds.

---

## 3. Make it reachable

A new Vercel project may have **Deployment Protection** switched on, which
gates every deployment behind a Vercel login. Anyone outside the team — a
judge, a reviewer, anyone you send the link to — gets a sign-in screen instead
of the site.

It is invisible from inside the account. Signed in, everything looks fine,
which is what makes it worth checking deliberately rather than discovering it
in front of an audience.

1. Vercel → the project → **Settings** → **Deployment Protection**
2. **Vercel Authentication** → **Only Preview Deployments**
3. **Save**

It takes effect immediately; no rebuild or redeploy.

**Why that value rather than *Disabled*.** Production becomes public, which is
the point, while branch previews still require a login. Preview URLs keep
serving the code they were built from forever, so a stale one can otherwise be
mistaken for the live site — leaving previews protected means nobody outside
the team can open one by accident. Choose **Disabled** only if previews also
need to be shareable.

> Password Protection and Trusted IPs are Pro/Enterprise features. Vercel
> Authentication is the setting that applies on a normal plan.

### Confirm it

Open the production URL in a **private/incognito window**. That is exactly
what a stranger sees, with no session — the only way to test this honestly.

Then, in that same window, open `/demo` and press **Run Full Demo**. Six green
steps confirm the other half of the question: the page is not just reachable,
it is reaching the backend.

---

## How the two connect

The browser never calls Render directly. `frontend/next.config.mjs` rewrites
`/api/*` to `BACKEND_ORIGIN` server-side, so:

- there is no CORS allow-list to keep in sync with the frontend's domain,
- an `https` page never tries to call an `http` API,
- the backend URL is not in the client bundle.

`frontend/lib/api.ts` defaults to same-origin in a production build, which is
what makes the proxy the default path. Local development is unchanged: with
`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` the browser calls the
backend directly, as before.

---

## Before you present

**Render's free tier sleeps after 15 minutes idle, and the next request takes
roughly 50 seconds to wake it.** In front of judges that reads as a broken
demo.

Open the demo URL a minute or two before you present and run it once. The
service then stays warm for 15 minutes of inactivity, and each subsequent run
takes about 11 seconds.

If you want to remove the risk entirely, Render's paid Starter tier does not
sleep.

## If something goes wrong

| Symptom | Cause |
|---|---|
| Every step fails instantly | `BACKEND_ORIGIN` unset, or has a trailing slash |
| Demo step 3 (zero-knowledge) fails, others pass | Node or the ZK artifacts missing from the image |
| First run hangs ~50s then works | Free-tier cold start, see above |
| Build fails on Vercel | Root Directory not set to `frontend` |
| Visitors see a Vercel login screen | Deployment Protection — see *Make it reachable* |
| Unsure which deployment you are looking at | Match the commit against the one on the Vercel dashboard — a preview URL keeps serving the code it was built from |
