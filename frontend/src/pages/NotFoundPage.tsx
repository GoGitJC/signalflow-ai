import { Link } from "react-router-dom";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center gap-6 px-6 text-center">
      <BrandLogo />
      <div>
        <p className="text-sm font-medium text-teal-800 dark:text-teal-300">404</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          That route is not part of the ForgeLinq dashboard. Head back to Overview or open Help.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        <Button asChild>
          <Link to="/">Back to dashboard</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/help">Help</Link>
        </Button>
      </div>
    </div>
  );
}
