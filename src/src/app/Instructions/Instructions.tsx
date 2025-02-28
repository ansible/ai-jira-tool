import * as React from 'react';
import {
  Card,
  CardTitle,
  CardBody,
  Title,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
  PageSection,
} from '@patternfly/react-core';

export interface ISupportProps {
  sampleProp?: string;
}

// eslint-disable-next-line prefer-const
let Instructions: React.FunctionComponent<ISupportProps> = () => (
  <PageSection hasBodyWrapper={true}>
    <Card isLarge>
        <CardTitle>
          <Title headingLevel="h4" size="xl">
            Instructions
          </Title>
        </CardTitle>
        <CardBody>
          <DescriptionList>
            <DescriptionListGroup>
              <DescriptionListTerm>Input structure</DescriptionListTerm>
              <DescriptionListDescription>

              </DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Variables</DescriptionListTerm>
              <DescriptionListDescription>TODO</DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>TODO</DescriptionListTerm>
              <DescriptionListDescription>TODO</DescriptionListDescription>
            </DescriptionListGroup>
          </DescriptionList>
        </CardBody>
      </Card>
  </PageSection>
);

export { Instructions };
