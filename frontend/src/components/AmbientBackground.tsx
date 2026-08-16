/**
 * Soft blurred monochrome blobs on an off-white base, fixed behind every
 * route. Purely decorative — pointer-events-none, negative z-index.
 */
export function AmbientBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-neutral-50">
      <div className="absolute -left-32 -top-32 h-[26rem] w-[26rem] rounded-full bg-neutral-300/40 blur-3xl" />
      <div className="absolute right-[-6rem] top-1/4 h-[30rem] w-[30rem] rounded-full bg-neutral-200/60 blur-3xl" />
      <div className="absolute bottom-[-8rem] left-1/4 h-[26rem] w-[26rem] rounded-full bg-neutral-300/30 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 h-72 w-72 rounded-full bg-neutral-200/50 blur-3xl" />
    </div>
  );
}
