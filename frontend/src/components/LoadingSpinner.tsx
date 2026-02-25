export default function LoadingSpinner({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-gray-400">
      <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      <span>{text}</span>
    </div>
  );
}
