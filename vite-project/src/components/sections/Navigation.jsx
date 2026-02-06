import { useNavigate, useLocation } from 'react-router'
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuIndicator,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  NavigationMenuViewport,
} from "@/components/ui/navigation-menu"

// const to easily change all the button styles
const buttonClass = "px-4 py-2 hover:bg-gray-200 rounded-md transition-colors";

/** Navigation bar with links to different sections of the site
 * - Sticky at the top of the page
 * - Smooth scroll to sections when clicked
 * - Navigates to home if not already there before scrolling ie. from project details page
*/
export default function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const scrollToSection = (id) => {
    // If not on home page, navigate to home first
    if (location.pathname !== '/') {
      navigate('/');
      // Wait a moment for the page to render, then scroll
      setTimeout(() => {
        const element = document.getElementById(id);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } else {
      // Already on home page, just scroll
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <div className="sticky top-0 z-50 flex justify-center bg-white/90 backdrop-blur-md shadow-md">
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <button
              onClick={() => scrollToSection('home')}
              className={buttonClass}
            >
              Home
            </button>
          </NavigationMenuItem>

          <NavigationMenuItem>
            <button
              onClick={() => scrollToSection('DataUpload')}
              className={buttonClass}
            >
              Data Upload
            </button>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>
  )
}