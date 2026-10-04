type LoadingProps = {
  message?: string;
};

export default function Loading({
  message = "Loading...",
}: LoadingProps) {
  return (
    <div className="state-message" role="status">
      {message}
    </div>
  );
}
