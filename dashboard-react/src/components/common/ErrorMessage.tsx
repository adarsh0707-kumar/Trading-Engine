type ErrorMessageProps = {
  message: string;
};

export default function ErrorMessage({
  message,
}: ErrorMessageProps) {
  return (
    <div className="state-message state-error" role="alert">
      {message}
    </div>
  );
}
