import FormSkeleton from "./components/FormSkeleton";

export default function Loading() {
  return (
    <div className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-gray-50/50">
      <div className="max-w-5xl mx-auto space-y-4">
        <FormSkeleton />
      </div>
    </div>
  );
}
