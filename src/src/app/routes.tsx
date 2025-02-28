import * as React from 'react';
import { Route, Routes } from 'react-router-dom';
import { Dashboard } from '@app/Dashboard/Dashboard';
import { Reports } from '@app/Reports/Reports';
import { About } from '@app/About/About';
import { Instructions } from '@app/Instructions/Instructions';
import { NotFound } from '@app/NotFound/NotFound';

export interface IAppRoute {
  label?: string; // Excluding the label will exclude the route from the nav sidebar in AppLayout
  /* eslint-disable @typescript-eslint/no-explicit-any */
  element: React.ReactElement;
  /* eslint-enable @typescript-eslint/no-explicit-any */
  exact?: boolean;
  path: string;
  title: string;
  routes?: undefined;
}

export interface IAppRouteGroup {
  label: string;
  routes: IAppRoute[];
}

export type AppRouteConfig = IAppRoute | IAppRouteGroup;

const routes: AppRouteConfig[] = [
  {
    element: <Dashboard />,
    exact: true,
    label: 'Dashboard',
    path: '/',
    title: 'AI Jira Tool | Upload',
  },
  {
    element: <Reports />,
    exact: true,
    label: 'Reports',
    path: '/reports',
    title: 'AI Jira Tool | Reports',
  },
  {
    element: <Instructions />,
    exact: true,
    label: 'Instructions',
    path: '/instructions',
    title: 'AI Jira Tool | Instructions',
  },
  {
    element: <About />,
    exact: true,
    label: 'About',
    path: '/about',
    title: 'AI Jira Tool | About Page',
  }
];

const flattenedRoutes: IAppRoute[] = routes.reduce(
  (flattened, route) => [...flattened, ...(route.routes ? route.routes : [route])],
  [] as IAppRoute[],
);

const AppRoutes = (): React.ReactElement => (
  <Routes>
    {flattenedRoutes.map(({ path, element }, idx) => (
      <Route path={path} element={element} key={idx} />
    ))}
    <Route element={<NotFound />} />
  </Routes>
);

export { AppRoutes, routes };
