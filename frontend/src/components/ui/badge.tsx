import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../shared/utils";
const badgeVariants = cva("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors", { variants: { variant: { default: "border-transparent bg-primary text-primary-foreground", secondary: "border-transparent bg-secondary text-secondary-foreground", outline: "text-foreground", human: "border-transparent bg-[hsl(14_64%_91%)] text-[hsl(14_46%_25%)]", ai: "border-transparent bg-[hsl(254_37%_91%)] text-[hsl(254_30%_32%)]" } }, defaultVariants: { variant: "default" } });
function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) { return <div className={cn(badgeVariants({ variant }), className)} {...props} />; }
export { Badge, badgeVariants };
